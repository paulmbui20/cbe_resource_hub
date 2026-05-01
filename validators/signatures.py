"""
validators/signatures.py
========================

Canonical file-signature registry.

Each entry in REGISTRY is a ``SignatureSpec`` describing:

* ``mime``       – The canonical MIME type string.
* ``label``      – Human-readable format name.
* ``max_size``   – Maximum permitted upload size in bytes.
* ``rules``      – One or more ``Rule`` objects that must ALL match
                   (AND-semantics within a single spec).  Multiple
                   ``SignatureSpec`` objects for the same MIME type are
                   OR-combined by the engine.

Rule types
----------
BytesRule
    Simple offset + bytes comparison, the building block of all
    classic magic-number detection.

MaskRule
    Offset + bytes compared after a bitwise AND with a mask, useful
    for formats whose header bytes have variable flag bits (e.g. MP3
    sync words).

ContainsRule
    Searches for a byte sequence anywhere within the inspection window
    (bounded search), used for container formats like MP4 (ftyp atom
    can appear at arbitrary offsets).

CallbackRule
    Arbitrary callable ``(bytes) -> bool`` for complex multi-step
    logic (e.g. ZIP-based formats that require structure walking).

All rule objects are intentionally frozen dataclasses so the engine
can safely cache / reuse them across requests.

Adding a new format
-------------------
1.  Add one or more ``SignatureSpec`` entries to REGISTRY.
2.  Update ``presets.py`` if you want a convenience preset validator.
3.  That's it — no other code changes required.
"""

from __future__ import annotations

import struct
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from typing import Callable, Final, Sequence

# ---------------------------------------------------------------------------
# Rule primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BytesRule:
    """Match ``expected`` bytes at ``offset`` in the file header."""

    offset: int
    expected: bytes

    def matches(self, data: bytes) -> bool:
        end = self.offset + len(self.expected)
        if len(data) < end:
            return False
        return data[self.offset : end] == self.expected


@dataclass(frozen=True, slots=True)
class MaskRule:
    """
    Match ``expected`` bytes at ``offset`` after applying ``mask``.

    Each byte of ``data[offset:offset+n]`` is ANDed with the corresponding
    mask byte before comparison.  Useful for format fields that carry version
    or flag bits which should be ignored during identification.
    """

    offset: int
    mask: bytes
    expected: bytes

    def __post_init__(self) -> None:
        if len(self.mask) != len(self.expected):
            raise ValueError("mask and expected must have the same length")

    def matches(self, data: bytes) -> bool:
        n = len(self.expected)
        end = self.offset + n
        if len(data) < end:
            return False
        window = data[self.offset : end]
        masked = bytes(b & m for b, m in zip(window, self.mask))
        return masked == self.expected


@dataclass(frozen=True, slots=True)
class ContainsRule:
    """
    Assert that ``needle`` appears within ``data[start:end]``.

    ``start`` and ``end`` define a *search window* inside the inspection
    buffer.  Use ``end=None`` to search to the end of the buffer.
    """

    needle: bytes
    start: int = 0
    end: int | None = None

    def matches(self, data: bytes) -> bool:
        window = data[self.start : self.end]
        return self.needle in window


@dataclass(frozen=True, slots=True)
class CallbackRule:
    """
    Delegate matching to an arbitrary callable.

    ``fn`` receives the full inspection buffer and returns ``True`` on match.
    """

    fn: Callable[[bytes], bool]

    def matches(self, data: bytes) -> bool:
        return self.fn(data)


# Type alias for the union of all rule types.
Rule = BytesRule | MaskRule | ContainsRule | CallbackRule


# ---------------------------------------------------------------------------
# SignatureSpec container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SignatureSpec:
    """
    Complete description of one file-format signature.

    Attributes
    ----------
    mime:
        The IANA MIME type (e.g. ``"image/png"``).
    label:
        Human-readable name shown in error messages.
    max_size:
        Maximum permitted upload size **in bytes**.  Set to ``0`` to
        disable size checking for this spec (not recommended).
    rules:
        Sequence of ``Rule`` objects.  **All** must match (AND logic).
        To express OR logic (e.g. multiple valid magic sequences for the
        same format), add a second ``SignatureSpec`` with the same
        ``mime``.
    """

    mime: str
    label: str
    max_size: int
    rules: Sequence[Rule] = field(default_factory=list)

    def matches(self, data: bytes) -> bool:
        """Return True iff every rule in *rules* matches *data*."""
        return all(rule.matches(data) for rule in self.rules)


# ---------------------------------------------------------------------------
# Size constants  (kept here so specs stay self-documenting)
# ---------------------------------------------------------------------------

_1_MB: Final[int] = 1 * 1024 * 1024
_1_5_MB: Final[int] = int(1.5 * 1024 * 1024)
_5_MB: Final[int] = 5 * 1024 * 1024
_10_MB: Final[int] = 10 * 1024 * 1024
_20_MB: Final[int] = 20 * 1024 * 1024
_25_MB: Final[int] = 25 * 1024 * 1024
_50_MB: Final[int] = 50 * 1024 * 1024
_100_MB: Final[int] = 100 * 1024 * 1024
_200_MB: Final[int] = 200 * 1024 * 1024
_500_MB: Final[int] = 500 * 1024 * 1024


# ---------------------------------------------------------------------------
# Complex callback helpers
# ---------------------------------------------------------------------------


def _is_zip_based(data: bytes) -> bool:
    """Return True if the buffer starts with a ZIP local-file header signature."""
    # PK\x03\x04 is the Local File Header signature (RFC 1951 / APPNOTE).
    return data[:4] == b"PK\x03\x04"


# ---------------------------------------------------------------------------
# ZIP-based document helpers
#
# THE CENTRAL-DIRECTORY PROBLEM
# ==============================
# The ZIP format places its Central Directory at the *end* of the archive,
# not the beginning.  Editors like LibreOffice and Microsoft Word always
# write compliant ZIPs, so the central directory of a real 5 MB DOCX may
# start at byte 4,900,000 — far beyond our 8 KB inspection window.
#
# zipfile.ZipFile raises BadZipFile when it cannot find the End-of-Central-
# Directory record within the supplied buffer, so simply wrapping the 8 KB
# header chunk in a BytesIO is unreliable for real-world uploads.
#
# SOLUTION: two-level detection
# ==============================
# 1. ``CallbackRule`` rules receive only the header ``bytes`` snapshot, as
#    always.  For ZIP-based formats the callback first attempts to open the
#    chunk as a ZIP (fast path — works when the whole file fits in 8 KB,
#    e.g. in tests).
# 2. When that fails with BadZipFile the callback falls back to a lightweight
#    **Local File Header scan**: it walks the raw bytes looking for PK\x03\x04
#    records and reads each entry's filename directly from the header fields
#    (no central directory required).  This is defined by APPNOTE §4.3.2 and
#    is how zip-recovery tools work.
#
# The LFH scan is intentionally bounded to the inspection buffer only, which
# means it sees the *first* entries of the archive — exactly what we need,
# because DOCX/XLSX/PPTX and ODF all place their identifying entries at the
# start of the archive (``[Content_Types].xml`` and ``word/``, ``xl/``,
# ``ppt/``, or the ODF ``mimetype`` entry are always written first).
# ---------------------------------------------------------------------------


def _lfh_entry_names(data: bytes) -> list[str]:
    """
    Extract ZIP entry names from Local File Header records in *data*.

    This parser does NOT require the Central Directory and therefore works
    on a truncated buffer (e.g. the first 8 KB of a multi-megabyte ZIP).

    Returns a list of filename strings decoded as UTF-8 (with replacement
    for any undecodable bytes).  May return an empty list if no valid LFH
    signatures are found.

    ZIP Local File Header layout (APPNOTE §4.3.2):
        Offset  Length  Field
        0       4       Signature  0x04034b50
        4       2       Version needed
        6       2       General purpose bit flag
        8       2       Compression method
        10      2       Last mod time
        12      2       Last mod date
        14      4       CRC-32
        18      4       Compressed size
        22      4       Uncompressed size
        26      2       File name length (n)
        28      2       Extra field length (m)
        30      n       File name
        30+n    m       Extra field
        30+n+m  …       File data
    """
    names: list[str] = []
    offset = 0
    limit = len(data)

    while offset + 30 <= limit:
        # Scan forward for the LFH signature.
        sig_pos = data.find(b"PK\x03\x04", offset)
        if sig_pos == -1 or sig_pos + 30 > limit:
            break

        try:
            fname_len = struct.unpack_from("<H", data, sig_pos + 26)[0]
            extra_len = struct.unpack_from("<H", data, sig_pos + 28)[0]
        except struct.error:
            break

        fname_start = sig_pos + 30
        fname_end = fname_start + fname_len

        if fname_end > limit:
            # Filename is cut off — we've reached the end of our buffer.
            break

        raw_name = data[fname_start:fname_end]
        names.append(raw_name.decode("utf-8", errors="replace"))

        # Advance past this header + filename + extra field.
        # (We do NOT advance past the file data — compressed size may be 0
        # for data descriptors, and we want to find the next LFH signature
        # by scanning, not by computing an offset through potentially huge
        # compressed data blocks.)
        offset = fname_end + extra_len

    return names


def _open_zip(data: bytes) -> zipfile.ZipFile | None:
    """
    Try to open *data* as a ZipFile.  Returns the open ZipFile on success
    or None if the data is not a valid/complete ZIP.

    Callers are responsible for closing the returned ZipFile.
    """
    try:
        return zipfile.ZipFile(BytesIO(data))
    except (zipfile.BadZipFile, EOFError, Exception):
        return None


def _zip_names(data: bytes) -> list[str]:
    """
    Return ZIP entry names from *data*, using whichever method succeeds.

    First tries the standard zipfile parser (requires central directory).
    Falls back to the LFH scanner (works on truncated buffers).
    """
    zf = _open_zip(data)
    if zf is not None:
        try:
            return zf.namelist()
        finally:
            zf.close()
    # Central directory not present in our chunk — use LFH scan.
    return _lfh_entry_names(data)


def _is_docx(data: bytes) -> bool:
    """
    Return True if *data* is (or begins with) a DOCX archive.

    Checks for the ``word/`` directory entry that all DOCX files must
    contain, using a central-directory scan when available and falling back
    to the Local File Header scan for large real-world uploads where only
    the first 8 KB of the file is inspected.
    """
    if not _is_zip_based(data):
        return False
    names = _zip_names(data)
    return any(n == "word/document.xml" or n.startswith("word/") for n in names)


def _is_xlsx(data: bytes) -> bool:
    """Return True if *data* is (or begins with) an XLSX archive."""
    if not _is_zip_based(data):
        return False
    names = _zip_names(data)
    return any(n.startswith("xl/") for n in names)


def _is_pptx(data: bytes) -> bool:
    """Return True if *data* is (or begins with) a PPTX archive."""
    if not _is_zip_based(data):
        return False
    names = _zip_names(data)
    return any(n.startswith("ppt/") for n in names)


def _is_odf(mime_suffix: str) -> Callable[[bytes], bool]:
    """
    Factory returning a callback that detects an ODF document by its
    mandatory ``mimetype`` entry.

    ODF specification §2.2.1 requires:
    * The ``mimetype`` file MUST be the first entry in the ZIP archive.
    * It MUST be stored uncompressed (method=0).
    * Its content MUST be the MIME type string without trailing whitespace.

    For the LFH-scan path (truncated buffer), we verify that the first
    entry name is ``mimetype`` and read its content directly from the
    local file data (uncompressed, so no decompression needed).
    """
    expected_content = f"application/vnd.oasis.opendocument.{mime_suffix}".encode()

    def _check(data: bytes) -> bool:
        if not _is_zip_based(data):
            return False

        # --- Fast path: full ZIP with central directory available --------
        zf = _open_zip(data)
        if zf is not None:
            try:
                info = zf.infolist()
                if not info or info[0].filename != "mimetype":
                    return False
                mt = zf.read("mimetype").strip()
                return mt == expected_content
            except Exception:
                return False
            finally:
                zf.close()

        # --- Fallback path: read mimetype entry directly from LFH -------
        # The ODF mimetype entry is always the first LFH and is uncompressed,
        # so we can read its content directly from the local file data bytes.
        if len(data) < 30:
            return False
        try:
            # Verify signature.
            if data[:4] != b"PK\x03\x04":
                return False
            fname_len = struct.unpack_from("<H", data, 26)[0]
            extra_len = struct.unpack_from("<H", data, 28)[0]
            uncomp_size = struct.unpack_from("<I", data, 22)[0]
            fname_start = 30
            fname_end = fname_start + fname_len
            if fname_end > len(data):
                return False
            fname = data[fname_start:fname_end].decode("utf-8", errors="replace")
            if fname != "mimetype":
                return False
            # Read the uncompressed content immediately after the header.
            content_start = fname_end + extra_len
            content_end = content_start + uncomp_size
            if content_end > len(data):
                return False
            mt = data[content_start:content_end].strip()
            return mt == expected_content
        except Exception:
            return False

    return _check


def _is_mp3_frame(data: bytes) -> bool:
    """
    Heuristic MP3 frame-header check.

    An MPEG audio frame starts with an 11-bit sync word (all ones).
    We check the first two bytes (0xFF + 0b111xxxxx) and validate that
    the MPEG version/layer bits are not 'reserved' values.

    data may also start with an ID3v2 tag, which we skip over.
    """
    buf = data

    # Skip ID3v2 tag if present.
    if buf[:3] == b"ID3":
        # ID3v2 size is encoded as 4 synchsafe integers at bytes 6–9.
        if len(buf) >= 10:
            sz = (
                ((buf[6] & 0x7F) << 21)
                | ((buf[7] & 0x7F) << 14)
                | ((buf[8] & 0x7F) << 7)
                | (buf[9] & 0x7F)
            )
            buf = buf[10 + sz :]

    if len(buf) < 4:
        return False

    # Sync word: first 11 bits all 1 (0xFF + high 3 bits of byte 1).
    if buf[0] != 0xFF or (buf[1] & 0xE0) != 0xE0:
        return False

    # MPEG version: bits 4–3 of byte 1.  0b01 is 'reserved' (invalid).
    mpeg_version = (buf[1] >> 3) & 0x03
    if mpeg_version == 0x01:
        return False

    # Layer: bits 2–1 of byte 1.  0b00 is 'reserved' (invalid).
    layer = (buf[1] >> 1) & 0x03
    if layer == 0x00:
        return False

    return True


def _mp4_has_ftyp(data: bytes) -> bool:
    """
    Walk the top-level ISO BMFF boxes to find an 'ftyp' box.

    MP4/QuickTime files are structured as a series of 4-byte-size + 4-byte-
    type boxes.  The ftyp box often appears at offset 4 but spec allows it
    to appear anywhere (e.g. after a 'wide' or 'skip' box).  We scan the
    first 1 KB.
    """
    offset = 0
    limit = min(len(data), 1024)
    while offset + 8 <= limit:
        try:
            box_size = struct.unpack_from(">I", data, offset)[0]
        except struct.error:
            break
        box_type = data[offset + 4 : offset + 8]
        if box_type == b"ftyp":
            return True
        if box_size < 8:
            # Malformed; stop scanning.
            break
        offset += box_size
    return False


def _mp4_brand_matches(brands: frozenset[bytes]) -> Callable[[bytes], bool]:
    """
    Return a callback that checks the ftyp major-brand (and compatible-brands)
    against *brands*.
    """

    def _check(data: bytes) -> bool:
        offset = 0
        limit = min(len(data), 1024)
        while offset + 8 <= limit:
            try:
                box_size = struct.unpack_from(">I", data, offset)[0]
            except struct.error:
                break
            box_type = data[offset + 4 : offset + 8]
            if box_type == b"ftyp" and box_size >= 12:
                major_brand = data[offset + 8 : offset + 12]
                # Also check compatible brands (every 4 bytes from offset+16).
                compat_raw = data[offset + 16 : offset + box_size]
                compat_brands = {
                    compat_raw[i : i + 4] for i in range(0, len(compat_raw) - 3, 4)
                }
                all_brands = {major_brand} | compat_brands
                if all_brands & brands:
                    return True
                break
            if box_size < 8:
                break
            offset += box_size
        return False

    return _check


# ---------------------------------------------------------------------------
# Signature registry
# ---------------------------------------------------------------------------
# Each SignatureSpec is independent.  The engine tries all specs that share a
# MIME type and reports a match if ANY of them fires (OR logic between specs,
# AND logic within a spec's rules list).

REGISTRY: tuple[SignatureSpec, ...] = (
    # =========================================================================
    # IMAGES
    # =========================================================================
    SignatureSpec(
        mime="image/jpeg",
        label="JPEG / JPG",
        max_size=_1_5_MB,
        rules=[BytesRule(0, b"\xff\xd8\xff")],
    ),
    # PNG — 8-byte magic.
    SignatureSpec(
        mime="image/png",
        label="PNG",
        max_size=_1_5_MB,
        rules=[BytesRule(0, b"\x89PNG\r\n\x1a\n")],
    ),
    # GIF87a / GIF89a.
    SignatureSpec(
        mime="image/gif",
        label="GIF",
        max_size=_1_5_MB,
        rules=[BytesRule(0, b"GIF87a")],
    ),
    SignatureSpec(
        mime="image/gif",
        label="GIF",
        max_size=_1_5_MB,
        rules=[BytesRule(0, b"GIF89a")],
    ),
    # WebP — RIFF header + WEBP marker at offset 8.
    SignatureSpec(
        mime="image/webp",
        label="WebP",
        max_size=_1_5_MB,
        rules=[
            BytesRule(0, b"RIFF"),
            BytesRule(8, b"WEBP"),
        ],
    ),
    # BMP.
    SignatureSpec(
        mime="image/bmp",
        label="BMP",
        max_size=_5_MB,
        rules=[BytesRule(0, b"BM")],
    ),
    # TIFF — little-endian byte order mark.
    SignatureSpec(
        mime="image/tiff",
        label="TIFF (little-endian)",
        max_size=_20_MB,
        rules=[BytesRule(0, b"II\x2a\x00")],
    ),
    # TIFF — big-endian byte order mark.
    SignatureSpec(
        mime="image/tiff",
        label="TIFF (big-endian)",
        max_size=_20_MB,
        rules=[BytesRule(0, b"MM\x00\x2a")],
    ),
    # AVIF — ISO BMFF ftyp box with 'avif' major brand.
    SignatureSpec(
        mime="image/avif",
        label="AVIF",
        max_size=_5_MB,
        rules=[CallbackRule(_mp4_brand_matches(frozenset({b"avif", b"avis"})))],
    ),
    # HEIC / HEIF — ISO BMFF ftyp with heic/heix/hevc brands.
    SignatureSpec(
        mime="image/heic",
        label="HEIC / HEIF",
        max_size=_10_MB,
        rules=[
            CallbackRule(
                _mp4_brand_matches(
                    frozenset(
                        {
                            b"heic",
                            b"heix",
                            b"hevc",
                            b"hevx",
                            b"heim",
                            b"heis",
                            b"hevm",
                            b"hevs",
                            b"mif1",
                        }
                    )
                )
            )
        ],
    ),
    # SVG — text XML; look for <svg after skipping optional BOM/whitespace.
    SignatureSpec(
        mime="image/svg+xml",
        label="SVG",
        max_size=_5_MB,
        rules=[CallbackRule(lambda d: b"<svg" in d[:256] or b"<SVG" in d[:256])],
    ),
    # ICO.
    SignatureSpec(
        mime="image/x-icon",
        label="ICO",
        max_size=_1_MB,
        rules=[BytesRule(0, b"\x00\x00\x01\x00")],
    ),
    # =========================================================================
    # VIDEO
    # =========================================================================
    # MP4 — ISO Base Media / MPEG-4 brands.
    SignatureSpec(
        mime="video/mp4",
        label="MP4",
        max_size=_500_MB,
        rules=[
            CallbackRule(
                _mp4_brand_matches(
                    frozenset(
                        {
                            b"mp41",
                            b"mp42",
                            b"isom",
                            b"iso2",
                            b"iso3",
                            b"iso4",
                            b"iso5",
                            b"iso6",
                            b"avc1",
                            b"dash",
                            b"MSNV",
                            b"NDAS",
                            b"NDSC",
                            b"NDSH",
                            b"NDSM",
                            b"NDSP",
                            b"NDSS",
                            b"NDXC",
                            b"NDXH",
                            b"NDXM",
                            b"NDXP",
                            b"NDXS",
                            b"F4V ",
                            b"F4P ",
                        }
                    )
                )
            )
        ],
    ),
    # QuickTime — ftyp brand 'qt  '.
    SignatureSpec(
        mime="video/quicktime",
        label="QuickTime / MOV",
        max_size=_500_MB,
        rules=[
            CallbackRule(_mp4_brand_matches(frozenset({b"qt  ", b"mqt ", b"mov "})))
        ],
    ),
    # QuickTime legacy: starts directly with 'moov', 'mdat', 'skip', 'wide'.
    SignatureSpec(
        mime="video/quicktime",
        label="QuickTime (legacy atom)",
        max_size=_500_MB,
        rules=[
            CallbackRule(
                lambda d: (
                    len(d) >= 8
                    and d[4:8] in {b"moov", b"mdat", b"wide", b"skip", b"free", b"pnot"}
                )
            )
        ],
    ),
    # WebM — EBML header with DocType "webm".
    SignatureSpec(
        mime="video/webm",
        label="WebM",
        max_size=_500_MB,
        rules=[BytesRule(0, b"\x1a\x45\xdf\xa3")],
    ),
    # OPUS in OGG container starts with OggS like Vorbis;
    # the Opus identifier is in the first page's header packet.
    # We keep a separate MIME for strict type requirements.
    # IMPORTANT: This spec must appear BEFORE the generic OGG audio/video
    # catch-alls because all three share the OggS magic; the Opus spec is
    # more specific (it also requires 'OpusHead' in the first 64 bytes).
    SignatureSpec(
        mime="audio/opus",
        label="Opus (OGG container)",
        max_size=_50_MB,
        rules=[
            BytesRule(0, b"OggS"),
            ContainsRule(b"OpusHead", start=0, end=64),
        ],
    ),
    # OGG video (Theora/Dirac containers share OGG magic).
    SignatureSpec(
        mime="video/ogg",
        label="OGG video",
        max_size=_200_MB,
        rules=[BytesRule(0, b"OggS")],
    ),
    # AVI — RIFF + AVI  marker.
    SignatureSpec(
        mime="video/x-msvideo",
        label="AVI",
        max_size=_500_MB,
        rules=[
            BytesRule(0, b"RIFF"),
            BytesRule(8, b"AVI "),
        ],
    ),
    # MKV / Matroska — EBML header.  Uses same start as WebM; DocType
    # distinguishes them but we keep both under broad EBML detection for
    # the video/x-matroska bucket.
    SignatureSpec(
        mime="video/x-matroska",
        label="Matroska / MKV",
        max_size=_500_MB,
        rules=[BytesRule(0, b"\x1a\x45\xdf\xa3")],
    ),
    # FLV.
    SignatureSpec(
        mime="video/x-flv",
        label="FLV",
        max_size=_200_MB,
        rules=[BytesRule(0, b"FLV\x01")],
    ),
    # =========================================================================
    # AUDIO
    # =========================================================================
    # MP3 — ID3v2 tag header.
    SignatureSpec(
        mime="audio/mpeg",
        label="MP3 (ID3v2)",
        max_size=_50_MB,
        rules=[BytesRule(0, b"ID3")],
    ),
    # MP3 — raw MPEG frame sync (no ID3 header).
    SignatureSpec(
        mime="audio/mpeg",
        label="MP3 (raw frame)",
        max_size=_50_MB,
        rules=[CallbackRule(_is_mp3_frame)],
    ),
    # MP3 — ID3v1 tag at start (rare but legal).
    SignatureSpec(
        mime="audio/mpeg",
        label="MP3 (ID3v1)",
        max_size=_50_MB,
        rules=[BytesRule(0, b"TAG")],
    ),
    # AAC — ADTS sync word (12 bits all-ones + layer=00 + CRC flag).
    SignatureSpec(
        mime="audio/aac",
        label="AAC (ADTS)",
        max_size=_50_MB,
        rules=[
            MaskRule(0, mask=b"\xff\xf6", expected=b"\xff\xf0"),
        ],
    ),
    # M4A — MPEG-4 audio (AAC in MP4 container) — ftyp brands.
    SignatureSpec(
        mime="audio/mp4",
        label="M4A / AAC in MP4",
        max_size=_50_MB,
        rules=[
            CallbackRule(
                _mp4_brand_matches(
                    frozenset(
                        {
                            b"M4A ",
                            b"M4B ",
                            b"M4P ",
                            b"mp41",
                            b"mp42",
                            b"isom",
                            b"f4a ",
                            b"f4b ",
                        }
                    )
                )
            )
        ],
    ),
    # OGG audio (Vorbis / Opus) — generic catch-all.
    # NOTE: audio/opus (with OpusHead marker) is detected first in the video
    # section ordering; this entry catches all remaining OGG streams
    # (Vorbis, Speex, FLAC-in-OGG, etc.).
    SignatureSpec(
        mime="audio/ogg",
        label="OGG audio (Vorbis/Opus)",
        max_size=_50_MB,
        rules=[BytesRule(0, b"OggS")],
    ),
    # FLAC.
    SignatureSpec(
        mime="audio/flac",
        label="FLAC",
        max_size=_100_MB,
        rules=[BytesRule(0, b"fLaC")],
    ),
    # WAV — RIFF + WAVE marker.
    SignatureSpec(
        mime="audio/wav",
        label="WAV",
        max_size=_50_MB,
        rules=[
            BytesRule(0, b"RIFF"),
            BytesRule(8, b"WAVE"),
        ],
    ),
    # AIFF — FORM + AIFF or AIFC marker.
    SignatureSpec(
        mime="audio/aiff",
        label="AIFF",
        max_size=_50_MB,
        rules=[
            BytesRule(0, b"FORM"),
            BytesRule(8, b"AIFF"),
        ],
    ),
    SignatureSpec(
        mime="audio/aiff",
        label="AIFC (compressed AIFF)",
        max_size=_50_MB,
        rules=[
            BytesRule(0, b"FORM"),
            BytesRule(8, b"AIFC"),
        ],
    ),
    # WMA / WMV — ASF header.
    SignatureSpec(
        mime="audio/x-ms-wma",
        label="WMA",
        max_size=_50_MB,
        rules=[BytesRule(0, b"\x30\x26\xb2\x75\x8e\x66\xcf\x11")],
    ),
    # AMR narrowband.
    SignatureSpec(
        mime="audio/amr",
        label="AMR",
        max_size=_10_MB,
        rules=[BytesRule(0, b"#!AMR\n")],
    ),
    # =========================================================================
    # DOCUMENTS
    # =========================================================================
    # PDF — %PDF header.
    SignatureSpec(
        mime="application/pdf",
        label="PDF",
        max_size=_25_MB,
        rules=[BytesRule(0, b"%PDF-")],
    ),
    # DOCX — ZIP + word/ directory.
    SignatureSpec(
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        label="DOCX (Word Open XML)",
        max_size=_25_MB,
        rules=[CallbackRule(_is_docx)],
    ),
    # XLSX — ZIP + xl/ directory.
    SignatureSpec(
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        label="XLSX (Excel Open XML)",
        max_size=_25_MB,
        rules=[CallbackRule(_is_xlsx)],
    ),
    # PPTX — ZIP + ppt/ directory.
    SignatureSpec(
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        label="PPTX (PowerPoint Open XML)",
        max_size=_25_MB,
        rules=[CallbackRule(_is_pptx)],
    ),
    # ODT — ODF text document.
    SignatureSpec(
        mime="application/vnd.oasis.opendocument.text",
        label="ODT (OpenDocument Text)",
        max_size=_25_MB,
        rules=[CallbackRule(_is_odf("text"))],
    ),
    # ODS — ODF spreadsheet.
    SignatureSpec(
        mime="application/vnd.oasis.opendocument.spreadsheet",
        label="ODS (OpenDocument Spreadsheet)",
        max_size=_25_MB,
        rules=[CallbackRule(_is_odf("spreadsheet"))],
    ),
    # ODP — ODF presentation.
    SignatureSpec(
        mime="application/vnd.oasis.opendocument.presentation",
        label="ODP (OpenDocument Presentation)",
        max_size=_25_MB,
        rules=[CallbackRule(_is_odf("presentation"))],
    ),
    # Legacy Microsoft Office compound document (DOC, XLS, PPT).
    # Signature: Compound File Binary (CFBF / OLE2).
    SignatureSpec(
        mime="application/msword",
        label="DOC (legacy Word / OLE2)",
        max_size=_25_MB,
        rules=[BytesRule(0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")],
    ),
    SignatureSpec(
        mime="application/vnd.ms-excel",
        label="XLS (legacy Excel / OLE2)",
        max_size=_25_MB,
        rules=[BytesRule(0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")],
    ),
    SignatureSpec(
        mime="application/vnd.ms-powerpoint",
        label="PPT (legacy PowerPoint / OLE2)",
        max_size=_25_MB,
        rules=[BytesRule(0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")],
    ),
    # RTF.
    SignatureSpec(
        mime="application/rtf",
        label="RTF",
        max_size=_10_MB,
        rules=[BytesRule(0, b"{\\rtf1")],
    ),
    # EPUB — ZIP containing META-INF/container.xml with epub marker.
    # NOTE: Must appear before the generic application/zip spec below because
    # EPUB files start with PK\x03\x04 and would otherwise be caught first.
    SignatureSpec(
        mime="application/epub+zip",
        label="EPUB",
        max_size=_25_MB,
        rules=[
            BytesRule(0, b"PK\x03\x04"),
            ContainsRule(b"epub", start=0, end=256),
        ],
    ),
    # =========================================================================
    # ARCHIVES
    # =========================================================================
    #
    # ORDERING RULE: The generic application/zip spec (PK\x03\x04 only) MUST
    # be the very last PK-magic entry in the registry.  All ZIP-based formats
    # (DOCX, XLSX, PPTX, ODT/ODS/ODP, EPUB) appear in the DOCUMENTS section
    # above and are more specific — their CallbackRules walk the ZIP structure
    # to confirm the container type.  The generic ZIP spec is the final catch-
    # all for plain archives with no recognisable Office/ODF structure.
    # ZIP.
    SignatureSpec(
        mime="application/zip",
        label="ZIP",
        max_size=_500_MB,
        rules=[BytesRule(0, b"PK\x03\x04")],
    ),
    # ZIP empty archive.
    SignatureSpec(
        mime="application/zip",
        label="ZIP (empty)",
        max_size=_500_MB,
        rules=[BytesRule(0, b"PK\x05\x06")],
    ),
    # ZIP spanned archive.
    SignatureSpec(
        mime="application/zip",
        label="ZIP (spanned)",
        max_size=_500_MB,
        rules=[BytesRule(0, b"PK\x07\x08")],
    ),
    # 7-Zip.
    SignatureSpec(
        mime="application/x-7z-compressed",
        label="7-Zip",
        max_size=_500_MB,
        rules=[BytesRule(0, b"7z\xbc\xaf\x27\x1c")],
    ),
    # RAR — version 1.5+.
    SignatureSpec(
        mime="application/x-rar-compressed",
        label="RAR (v1.5+)",
        max_size=_500_MB,
        rules=[BytesRule(0, b"Rar!\x1a\x07\x00")],
    ),
    # RAR — version 5.0+.
    SignatureSpec(
        mime="application/x-rar-compressed",
        label="RAR (v5+)",
        max_size=_500_MB,
        rules=[BytesRule(0, b"Rar!\x1a\x07\x01\x00")],
    ),
    # TAR (POSIX ustar).
    SignatureSpec(
        mime="application/x-tar",
        label="TAR (ustar)",
        max_size=_500_MB,
        rules=[BytesRule(257, b"ustar")],
    ),
    # GZip (also covers .tar.gz).
    SignatureSpec(
        mime="application/gzip",
        label="GZip",
        max_size=_500_MB,
        rules=[BytesRule(0, b"\x1f\x8b")],
    ),
    # Bzip2 (also covers .tar.bz2).
    SignatureSpec(
        mime="application/x-bzip2",
        label="BZip2",
        max_size=_500_MB,
        rules=[BytesRule(0, b"BZh")],
    ),
    # XZ (also covers .tar.xz).
    SignatureSpec(
        mime="application/x-xz",
        label="XZ",
        max_size=_500_MB,
        rules=[BytesRule(0, b"\xfd7zXZ\x00")],
    ),
    # Zstandard.
    SignatureSpec(
        mime="application/zstd",
        label="Zstandard",
        max_size=_500_MB,
        rules=[BytesRule(0, b"\x28\xb5\x2f\xfd")],
    ),
    # LZ4.
    SignatureSpec(
        mime="application/x-lz4",
        label="LZ4",
        max_size=_500_MB,
        rules=[BytesRule(0, b"\x04\x22\x4d\x18")],
    ),
)
