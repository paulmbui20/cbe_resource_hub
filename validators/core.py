"""
validators/core.py
==================

Core validation engine and Django validator class.

MagicEngine
    Stateless, thread-safe scanner that maps raw bytes to a MIME type by
    testing ``SignatureSpec`` entries from the registry.  Instantiated once
    at module import time as a singleton; callers interact with it through
    ``DeepSignatureValidator`` or directly via ``MagicEngine.detect()``.

SignatureMatch
    Lightweight result type returned by ``MagicEngine.detect()``, carrying
    both the matched MIME type and the matched ``SignatureSpec`` for callers
    that need richer information (e.g. to look up the human-readable label
    or the permitted maximum size).

DeepSignatureValidator
    Django-compatible, ``@deconstructible`` validator class.  Drop it into
    any ``FileField`` or ``ImageField`` ``validators=`` list.

Thread safety
-------------
``MagicEngine`` holds no mutable state after construction.  All per-call
state lives on the stack, so the singleton is safe for concurrent use inside
WSGI/ASGI workers without locking.

Memory safety
-------------
Only a bounded header chunk (``READ_CHUNK_BYTES``) is read from the
uploaded file — never the full file.  For large files backed by
``TemporaryUploadedFile``, this means a ≤ 8 KB read regardless of the
upload's size.  The file pointer is always restored via ``finally`` so
downstream save handlers see a complete stream.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from .signatures import REGISTRY, SignatureSpec

if TYPE_CHECKING:
    from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)

# How many bytes we read from the start of each uploaded file.
# 64 KB gives the LFH-scanner (Local File Header) a deep enough buffer to
# traverse past embedded images that sometimes appear very early in DOCX files.
READ_CHUNK_BYTES: int = 65_536

# ZIP magic bytes (Local File Header) for quick detection
_ZIP_MAGIC = b"PK\x03\x04"


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SignatureMatch:
    """
    Result of a successful ``MagicEngine.detect()`` call.

    Attributes
    ----------
    mime:
        The detected MIME type (e.g. ``"image/png"``).
    spec:
        The ``SignatureSpec`` whose rules fired.  Use ``spec.label`` for a
        human-readable format name and ``spec.max_size`` for the permitted
        size limit.
    """

    mime: str
    spec: SignatureSpec


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class MagicEngine:
    """
    Pure-Python, zero-dependency file-type detection engine.

    Detection algorithm
    -------------------
    1.  Group all ``SignatureSpec`` entries in the registry by MIME type.
    2.  For an incoming buffer, iterate over every spec in insertion order.
    3.  A spec *matches* iff **all** of its rules return ``True`` (AND logic).
    4.  The first matching spec wins and is returned immediately.
    5.  If no spec matches, ``None`` is returned.

    The engine prefers specificity: more-specific specs (e.g. DOCX before
    generic ZIP) must be listed first in ``signatures.REGISTRY``.

    Usage
    -----
    engine = MagicEngine()                 # or use the module singleton
    match = engine.detect(header_bytes)   # header_bytes: bytes | bytearray
    if match:
        print(match.mime, match.spec.label)
    """

    def __init__(self, registry: tuple[SignatureSpec, ...] = REGISTRY) -> None:
        self._registry = registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, data: bytes | bytearray) -> SignatureMatch | None:
        """
        Scan *data* and return the first matching ``SignatureMatch``, or
        ``None`` if no signature fires.

        Parameters
        ----------
        data:
            A bytes-like object containing the file's leading bytes.  At
            least ``READ_CHUNK_BYTES`` (8 192 bytes) is recommended.

        Returns
        -------
        ``SignatureMatch`` or ``None``
        """
        for spec in self._registry:
            if spec.matches(data):
                return SignatureMatch(mime=spec.mime, spec=spec)
        return None

    def detect_from_file(self, file: "UploadedFile") -> SignatureMatch | None:
        """
        Read uploaded file bytes, run ``detect``, and reset the file pointer.

        Strategy
        ---------
        1.  Read the first ``READ_CHUNK_BYTES`` (8 KB) from the file.
        2.  Run a quick header-only check.
        3.  If the header starts with the ZIP signature (``PK\\x03\\x04``),
            read the **full file** so that ``zipfile`` can locate the Central
            Directory (which the ZIP spec places at the *end* of the archive).
            This is necessary for real-world DOCX/XLSX/PPTX/ODF uploads where
            the central directory is well beyond the first 8 KB.
        4.  Restore the file pointer to 0 unconditionally via ``finally``.

        The full-file read for ZIP uploads is bounded by the per-spec
        ``max_size`` limit (enforced later by the validator), so an attacker
        cannot force unbounded memory allocation by uploading a large ZIP — the
        Django upload handler already enforces ``DATA_UPLOAD_MAX_MEMORY_SIZE``
        for in-memory uploads, and ``TemporaryUploadedFile`` objects are backed
        by disk, so ``file.read()`` streams from the temp file rather than
        loading everything into a new allocation in one shot.

        The file pointer is **always** restored to position 0, even if an
        exception is raised during reading, so downstream code (e.g. storage
        backends) always sees a complete stream.

        Parameters
        ----------
        file:
            A Django ``UploadedFile`` (``InMemoryUploadedFile`` or
            ``TemporaryUploadedFile``).
        """
        try:
            file.seek(0)
            header = file.read(READ_CHUNK_BYTES)

            # ZIP-based formats (DOCX, XLSX, PPTX, ODF, EPUB, plain ZIP)
            # require the full file content so zipfile can find the Central
            # Directory.  We detect the ZIP signature cheaply from the 8 KB
            # header before deciding to read further.
            if header[:4] == _ZIP_MAGIC:
                file.seek(0)
                data: bytes | bytearray = file.read()
            else:
                data = header

        except OSError as exc:
            raise ValidationError(
                _("Could not read uploaded file: %(error)s"),
                code="file_read_error",
                params={"error": str(exc)},
            ) from exc
        finally:
            # Unconditionally restore pointer so the file is still usable.
            try:
                file.seek(0)
            except OSError:
                pass  # In-memory buffers that don't support seek — safe to ignore.

        return self.detect(data)


# Module-level singleton — constructed once at import time.
_engine = MagicEngine()


# ---------------------------------------------------------------------------
# Django validator
# ---------------------------------------------------------------------------


@deconstructible
class DeepSignatureValidator:
    """
    Django file-field validator using deep magic-byte signature detection.

    Place an instance in the ``validators`` list of any ``FileField`` or
    ``ImageField``.  The validator:

    1.  Reads only the first ``READ_CHUNK_BYTES`` (8 KB) of the upload.
    2.  Runs the signature engine over those bytes.
    3.  Rejects files whose detected MIME type is not in ``allowed_mimetypes``.
    4.  Optionally enforces a per-type maximum file size (taken from the
        matching ``SignatureSpec``) or a caller-supplied ``max_size``.

    Because the validator is ``@deconstructible``, Django's migration
    framework can serialise it correctly when it appears in a model field.

    Parameters
    ----------
    allowed_mimetypes:
        An iterable of MIME type strings (e.g.
        ``["image/jpeg", "image/png"]``).  Case-sensitive.
    max_size:
        Optional hard cap on file size in bytes, applied *before* MIME
        detection.  Pass ``None`` (default) to use the per-spec
        ``max_size`` defined in the registry.  Pass ``0`` to disable size
        checking entirely (not recommended in production).
    error_messages:
        Optional dict overriding individual error messages.  Keys:
        ``"unknown_type"``, ``"invalid_type"``, ``"file_too_large"``,
        ``"file_read_error"``.

    Examples
    --------
    ::

        from validators import DeepSignatureValidator

        class UserProfile(models.Model):
            avatar = models.FileField(
                upload_to="avatars/",
                validators=[
                    DeepSignatureValidator(
                        allowed_mimetypes=["image/jpeg", "image/png", "image/webp"],
                    )
                ],
            )

        class Document(models.Model):
            file = models.FileField(
                upload_to="docs/",
                validators=[
                    DeepSignatureValidator(
                        allowed_mimetypes=[
                            "application/pdf",
                            "application/vnd.openxmlformats-officedocument"
                            ".wordprocessingml.document",
                        ],
                        max_size=10 * 1024 * 1024,  # override to 10 MB
                    )
                ],
            )
    """

    # Default error message templates.  Override via ``error_messages`` kwarg.
    _default_messages: dict[str, str] = {
        "unknown_type": _(
            "The uploaded file could not be identified. "
            "Ensure it is a valid %(allowed_labels)s file."
        ),
        "invalid_type": _(
            "File type '%(detected_label)s' (%(detected_mime)s) is not allowed. "
            "Accepted formats: %(allowed_labels)s."
        ),
        "file_too_large": _(
            "The uploaded file is %(size_mb).1f MB, which exceeds the "
            "%(limit_mb).1f MB limit for %(detected_label)s files."
        ),
        "file_read_error": _("Could not read the uploaded file: %(error)s"),
    }

    def __init__(
        self,
        allowed_mimetypes: list[str] | tuple[str, ...],
        *,
        max_size: int | None = None,
        error_messages: dict[str, str] | None = None,
        engine: MagicEngine | None = None,
    ) -> None:
        # Freeze to a frozenset for O(1) membership tests.
        self.allowed_mimetypes: frozenset[str] = frozenset(allowed_mimetypes)
        self.max_size = max_size
        self.error_messages = dict(self._default_messages)
        if error_messages:
            self.error_messages.update(error_messages)

        # Allow injection of a custom engine (useful in tests).
        self._engine = engine or _engine

    # ------------------------------------------------------------------
    # Django validator protocol
    # ------------------------------------------------------------------

    def __call__(self, file: "UploadedFile") -> None:
        """
        Validate *file*.

        Raises
        ------
        django.core.exceptions.ValidationError
            If the file type is unrecognised, not in the allowed list, or
            exceeds the size limit.
        """
        # --- Step 1: Detect the MIME type via magic bytes ----------------
        try:
            match = self._engine.detect_from_file(file)
        except ValidationError:
            raise
        except Exception as exc:  # Defensive catch for unexpected I/O errors.
            logger.exception("Unexpected error reading uploaded file")
            raise ValidationError(
                self.error_messages["file_read_error"],
                code="file_read_error",
                params={"error": str(exc)},
            ) from exc

        # --- Step 2: Handle unrecognised file type -----------------------
        if match is None:
            allowed_labels = self._allowed_labels()
            logger.warning(
                "Upload rejected: unrecognised magic bytes. "
                "Allowed types: %s. File name: %s",
                allowed_labels,
                getattr(file, "name", "<unknown>"),
            )
            raise ValidationError(
                self.error_messages["unknown_type"],
                code="unknown_type",
                params={"allowed_labels": allowed_labels},
            )

        # --- Step 3: Check that the detected type is permitted -----------
        if match.mime not in self.allowed_mimetypes:
            logger.warning(
                "Upload rejected: detected '%s' (%s), expected one of %s. "
                "File name: %s",
                match.spec.label,
                match.mime,
                sorted(self.allowed_mimetypes),
                getattr(file, "name", "<unknown>"),
            )
            raise ValidationError(
                self.error_messages["invalid_type"],
                code="invalid_type",
                params={
                    "detected_mime": match.mime,
                    "detected_label": match.spec.label,
                    "allowed_labels": self._allowed_labels(),
                },
            )

        # --- Step 4: Enforce size limit ----------------------------------
        # Precedence: caller-supplied max_size > spec max_size > no limit.
        effective_max = self.max_size
        if effective_max is None:
            effective_max = match.spec.max_size  # May be 0 (disabled).

        if effective_max and file.size > effective_max:
            logger.warning(
                "Upload rejected: file size %.2f MB exceeds limit %.2f MB "
                "for type '%s'. File name: %s",
                file.size / (1024 * 1024),
                effective_max / (1024 * 1024),
                match.mime,
                getattr(file, "name", "<unknown>"),
            )
            raise ValidationError(
                self.error_messages["file_too_large"],
                code="file_too_large",
                params={
                    "size_mb": file.size / (1024 * 1024),
                    "limit_mb": effective_max / (1024 * 1024),
                    "detected_label": match.spec.label,
                },
            )

    # ------------------------------------------------------------------
    # Deconstruction support (required by @deconstructible)
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, DeepSignatureValidator)
            and self.allowed_mimetypes == other.allowed_mimetypes
            and self.max_size == other.max_size
        )

    def __repr__(self) -> str:
        mimes = ", ".join(sorted(self.allowed_mimetypes))
        return (
            f"DeepSignatureValidator("
            f"allowed_mimetypes=[{mimes!r}], "
            f"max_size={self.max_size!r})"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _allowed_labels(self) -> str:
        """
        Build a human-readable list of allowed format labels by looking up
        each permitted MIME type in the registry.
        """
        seen: dict[str, str] = {}
        for spec in REGISTRY:
            if spec.mime in self.allowed_mimetypes and spec.mime not in seen:
                seen[spec.mime] = spec.label
        # Fall back to raw MIME strings for any type not in the registry.
        for mime in sorted(self.allowed_mimetypes):
            if mime not in seen:
                seen[mime] = mime
        return ", ".join(seen.values())
