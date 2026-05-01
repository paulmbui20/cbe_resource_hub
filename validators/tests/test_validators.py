"""
tests/test_validators.py
========================

Comprehensive test suite for the deep-signature validator library.

Tests are written with pytest and do NOT require Django to be fully
configured (they import only the pure-Python engine layer).  For the Django
validator class tests (``TestDeepSignatureValidator``), a minimal Django
setup is bootstrapped inside ``conftest.py`` or at the top of this file.

Run with:  pytest tests/test_validators.py -v
"""

from __future__ import annotations

import io
import struct
import zipfile
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Minimal Django bootstrap (no database required).
# ---------------------------------------------------------------------------
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        USE_I18N=False,
        DATABASES={},
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )
    django.setup()

# Now we can import our validators.
from validators.core import MagicEngine, DeepSignatureValidator

from validators.signatures import (
    BytesRule,
    MaskRule,
    ContainsRule,
    CallbackRule,
    REGISTRY,
)
from validators.presets import (
    validate_image_file,
    validate_video_file,
    validate_audio_file,
    validate_document_file,
    validate_archive_file,
)
from django.core.exceptions import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_file(data: bytes, size: int | None = None, name: str = "test.bin"):
    """Return a mock UploadedFile backed by *data*."""
    buf = io.BytesIO(data)
    buf.name = name
    mock = MagicMock()
    mock.read.side_effect = buf.read
    mock.seek.side_effect = buf.seek
    mock.tell.side_effect = buf.tell
    mock.name = name
    mock.size = size if size is not None else len(data)
    # Make the mock callable like a real file for seek(0).
    return mock


def _make_real_file(data: bytes, size: int | None = None, name: str = "test.bin"):
    """Return a real BytesIO wrapped to look like an UploadedFile."""

    class FakeUploadedFile:
        def __init__(self, data, size, name):
            self._buf = io.BytesIO(data)
            self.size = size if size is not None else len(data)
            self.name = name

        def read(self, n=-1):
            return self._buf.read(n)

        def seek(self, pos, whence=0):
            return self._buf.seek(pos, whence)

        def tell(self):
            return self._buf.tell()

    return FakeUploadedFile(data, size if size is not None else len(data), name)


# ---------------------------------------------------------------------------
# Canonical magic bytes for each tested format
# ---------------------------------------------------------------------------

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 28
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
GIF87_BYTES = b"GIF87a" + b"\x00" * 26
GIF89_BYTES = b"GIF89a" + b"\x00" * 26
WEBP_BYTES = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 20
BMP_BYTES = b"BM" + b"\x00" * 30
TIFF_LE = b"II\x2a\x00" + b"\x00" * 28
TIFF_BE = b"MM\x00\x2a" + b"\x00" * 28
ICO_BYTES = b"\x00\x00\x01\x00" + b"\x00" * 28
SVG_BYTES = (
    b"<?xml version='1.0'?><svg xmlns='http://www.w3.org/2000/svg'>" + b"\x00" * 100
)

WEBM_BYTES = b"\x1a\x45\xdf\xa3" + b"\x00" * 28
OGG_BYTES = b"OggS" + b"\x00" * 28
OPUS_BYTES = b"OggS" + b"\x00" * 24 + b"OpusHead"
AVI_BYTES = b"RIFF\x00\x00\x00\x00AVI " + b"\x00" * 20
FLV_BYTES = b"FLV\x01" + b"\x00" * 28

ID3_MP3 = b"ID3" + b"\x00" * 7 + b"\xff\xfb" + b"\x00" * 18
RAW_MP3 = b"\xff\xfb\x90\x00" + b"\x00" * 28  # sync + MPEG1, Layer III, no CRC
FLAC_BYTES = b"fLaC" + b"\x00" * 28
WAV_BYTES = b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 20
AIFF_BYTES = b"FORM\x00\x00\x00\x00AIFF" + b"\x00" * 20
AIFC_BYTES = b"FORM\x00\x00\x00\x00AIFC" + b"\x00" * 20
WMA_BYTES = b"\x30\x26\xb2\x75\x8e\x66\xcf\x11" + b"\x00" * 24
AMR_BYTES = b"#!AMR\n" + b"\x00" * 26

PDF_BYTES = b"%PDF-1.7\n" + b"\x00" * 23
RTF_BYTES = b"{\\rtf1" + b"\x00" * 26
OLE2_BYTES = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 24

ZIP_BYTES = b"PK\x03\x04" + b"\x00" * 29
SEVENZIP_BYTES = b"7z\xbc\xaf\x27\x1c" + b"\x00" * 26
RAR_V15 = b"Rar!\x1a\x07\x00" + b"\x00" * 25
RAR_V5 = b"Rar!\x1a\x07\x01\x00" + b"\x00" * 24
GZIP_BYTES = b"\x1f\x8b" + b"\x00" * 30
BZ2_BYTES = b"BZh" + b"\x00" * 29
XZ_BYTES = b"\xfd7zXZ\x00" + b"\x00" * 26
ZSTD_BYTES = b"\x28\xb5\x2f\xfd" + b"\x00" * 28
LZ4_BYTES = b"\x04\x22\x4d\x18" + b"\x00" * 28

# TAR: magic at offset 257.
TAR_BYTES = b"\x00" * 257 + b"ustar" + b"\x00" * (8192 - 262)


def _make_mp4(brand: bytes) -> bytes:
    """Build a minimal MP4 ftyp box with the given 4-byte brand."""
    ftyp = b"ftyp" + brand + b"\x00\x00\x00\x00"  # type + major + minor version
    size = struct.pack(">I", 8 + len(ftyp))
    return size + ftyp + b"\x00" * (8192 - 8 - len(ftyp))


def _make_zip_with_entries(*entries: str) -> bytes:
    """Create an in-memory ZIP with empty files at the given paths."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for entry in entries:
            zf.writestr(entry, b"")
    return buf.getvalue()


def _make_odf(mime_suffix: str) -> bytes:
    """Create a minimal ODF-compliant ZIP."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
        # ODF §2.2.1: 'mimetype' must be first entry, uncompressed.
        zf.writestr(
            zipfile.ZipInfo("mimetype"),
            f"application/vnd.oasis.opendocument.{mime_suffix}",
        )
        zf.writestr("META-INF/manifest.xml", b"")
    return buf.getvalue()


# ===========================================================================
# Unit tests: Rule primitives
# ===========================================================================


class TestBytesRule:
    def test_exact_match(self):
        rule = BytesRule(0, b"\xff\xd8\xff")
        assert rule.matches(b"\xff\xd8\xff\xe0" + b"\x00" * 28)

    def test_offset_match(self):
        rule = BytesRule(4, b"ftyp")
        assert rule.matches(b"\x00\x00\x00\x1c" + b"ftyp" + b"\x00" * 24)

    def test_mismatch(self):
        rule = BytesRule(0, b"\xff\xd8\xff")
        assert not rule.matches(b"\x89PNG\r\n\x1a\n")

    def test_data_too_short(self):
        rule = BytesRule(0, b"\xff\xd8\xff\xe0")
        assert not rule.matches(b"\xff\xd8")

    def test_offset_beyond_data(self):
        rule = BytesRule(100, b"ftyp")
        assert not rule.matches(b"\x00" * 10)


class TestMaskRule:
    def test_aac_sync_word(self):
        # ADTS sync: 0xFFF? where ? can be 0 or 1.
        rule = MaskRule(0, mask=b"\xff\xf6", expected=b"\xff\xf0")
        assert rule.matches(b"\xff\xf1" + b"\x00" * 30)  # 0xFFF1 & 0xFFF6 = 0xFFF0
        assert rule.matches(b"\xff\xf0" + b"\x00" * 30)
        assert not rule.matches(b"\xff\xe0" + b"\x00" * 30)

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            MaskRule(0, mask=b"\xff\xff", expected=b"\xff")

    def test_data_too_short(self):
        rule = MaskRule(0, mask=b"\xff\xff", expected=b"\xff\xfb")
        assert not rule.matches(b"\xff")


class TestContainsRule:
    def test_found(self):
        rule = ContainsRule(b"WEBP", start=8, end=16)
        assert rule.matches(b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 20)

    def test_not_found(self):
        rule = ContainsRule(b"WEBP", start=8, end=16)
        assert not rule.matches(b"RIFF\x00\x00\x00\x00MP4 " + b"\x00" * 20)

    def test_no_end_limit(self):
        rule = ContainsRule(b"needle")
        assert rule.matches(b"\x00" * 100 + b"needle" + b"\x00" * 100)


class TestCallbackRule:
    def test_true_callback(self):
        rule = CallbackRule(lambda d: True)
        assert rule.matches(b"anything")

    def test_false_callback(self):
        rule = CallbackRule(lambda d: False)
        assert not rule.matches(b"anything")

    def test_receives_full_data(self):
        captured = []
        rule = CallbackRule(lambda d: captured.append(d) or True)
        data = b"hello world"
        rule.matches(data)
        assert captured[0] == data


# ===========================================================================
# Unit tests: MagicEngine detection
# ===========================================================================


class TestMagicEngine:
    engine = MagicEngine()

    def _detect(self, data: bytes):
        return self.engine.detect(data)

    # -- Images --

    def test_jpeg(self):
        m = self._detect(JPEG_BYTES)
        assert m and m.mime == "image/jpeg"

    def test_png(self):
        m = self._detect(PNG_BYTES)
        assert m and m.mime == "image/png"

    def test_gif87(self):
        m = self._detect(GIF87_BYTES)
        assert m and m.mime == "image/gif"

    def test_gif89(self):
        m = self._detect(GIF89_BYTES)
        assert m and m.mime == "image/gif"

    def test_webp(self):
        m = self._detect(WEBP_BYTES)
        assert m and m.mime == "image/webp"

    def test_bmp(self):
        m = self._detect(BMP_BYTES)
        assert m and m.mime == "image/bmp"

    def test_tiff_le(self):
        m = self._detect(TIFF_LE)
        assert m and m.mime == "image/tiff"

    def test_tiff_be(self):
        m = self._detect(TIFF_BE)
        assert m and m.mime == "image/tiff"

    def test_ico(self):
        m = self._detect(ICO_BYTES)
        assert m and m.mime == "image/x-icon"

    def test_svg(self):
        m = self._detect(SVG_BYTES)
        assert m and m.mime == "image/svg+xml"

    def test_avif(self):
        m = self._detect(_make_mp4(b"avif"))
        assert m and m.mime == "image/avif"

    def test_heic(self):
        m = self._detect(_make_mp4(b"heic"))
        assert m and m.mime == "image/heic"

    # -- Video --

    def test_mp4_isom(self):
        m = self._detect(_make_mp4(b"isom"))
        assert m and m.mime == "video/mp4"

    def test_mp4_mp41(self):
        m = self._detect(_make_mp4(b"mp41"))
        assert m and m.mime == "video/mp4"

    def test_quicktime(self):
        m = self._detect(_make_mp4(b"qt  "))
        assert m and m.mime == "video/quicktime"

    def test_webm(self):
        m = self._detect(WEBM_BYTES)
        assert m and m.mime in {"video/webm", "video/x-matroska"}

    def test_ogg_video(self):
        m = self._detect(OGG_BYTES)
        assert m and m.mime in {"video/ogg", "audio/ogg", "audio/opus"}

    def test_avi(self):
        m = self._detect(AVI_BYTES)
        assert m and m.mime == "video/x-msvideo"

    def test_flv(self):
        m = self._detect(FLV_BYTES)
        assert m and m.mime == "video/x-flv"

    # -- Audio --

    def test_mp3_id3(self):
        m = self._detect(ID3_MP3)
        assert m and m.mime == "audio/mpeg"

    def test_mp3_raw_frame(self):
        m = self._detect(RAW_MP3)
        assert m and m.mime == "audio/mpeg"

    def test_flac(self):
        m = self._detect(FLAC_BYTES)
        assert m and m.mime == "audio/flac"

    def test_wav(self):
        m = self._detect(WAV_BYTES)
        assert m and m.mime == "audio/wav"

    def test_aiff(self):
        m = self._detect(AIFF_BYTES)
        assert m and m.mime == "audio/aiff"

    def test_aifc(self):
        m = self._detect(AIFC_BYTES)
        assert m and m.mime == "audio/aiff"

    def test_wma(self):
        m = self._detect(WMA_BYTES)
        assert m and m.mime == "audio/x-ms-wma"

    def test_amr(self):
        m = self._detect(AMR_BYTES)
        assert m and m.mime == "audio/amr"

    def test_opus(self):
        m = self._detect(OPUS_BYTES)
        assert m and m.mime == "audio/opus"

    # -- Documents --

    def test_pdf(self):
        m = self._detect(PDF_BYTES)
        assert m and m.mime == "application/pdf"

    def test_docx(self):
        data = _make_zip_with_entries("word/document.xml", "[Content_Types].xml")
        m = self._detect(data)
        assert m and m.mime == (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    def test_xlsx(self):
        data = _make_zip_with_entries("xl/workbook.xml", "[Content_Types].xml")
        m = self._detect(data)
        assert m and m.mime == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_pptx(self):
        data = _make_zip_with_entries("ppt/presentation.xml", "[Content_Types].xml")
        m = self._detect(data)
        assert m and m.mime == (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

    def test_odt(self):
        m = self._detect(_make_odf("text"))
        assert m and m.mime == "application/vnd.oasis.opendocument.text"

    def test_ods(self):
        m = self._detect(_make_odf("spreadsheet"))
        assert m and m.mime == "application/vnd.oasis.opendocument.spreadsheet"

    def test_odp(self):
        m = self._detect(_make_odf("presentation"))
        assert m and m.mime == "application/vnd.oasis.opendocument.presentation"

    def test_ole2_compound(self):
        m = self._detect(OLE2_BYTES)
        # OLE2 signature matches DOC/XLS/PPT — any of those is valid.
        assert m and m.mime in {
            "application/msword",
            "application/vnd.ms-excel",
            "application/vnd.ms-powerpoint",
        }

    def test_rtf(self):
        m = self._detect(RTF_BYTES)
        assert m and m.mime == "application/rtf"

    # -- Archives --

    def test_zip(self):
        m = self._detect(ZIP_BYTES)
        assert m and m.mime == "application/zip"

    def test_7zip(self):
        m = self._detect(SEVENZIP_BYTES)
        assert m and m.mime == "application/x-7z-compressed"

    def test_rar_v15(self):
        m = self._detect(RAR_V15)
        assert m and m.mime == "application/x-rar-compressed"

    def test_rar_v5(self):
        m = self._detect(RAR_V5)
        assert m and m.mime == "application/x-rar-compressed"

    def test_gzip(self):
        m = self._detect(GZIP_BYTES)
        assert m and m.mime == "application/gzip"

    def test_bzip2(self):
        m = self._detect(BZ2_BYTES)
        assert m and m.mime == "application/x-bzip2"

    def test_xz(self):
        m = self._detect(XZ_BYTES)
        assert m and m.mime == "application/x-xz"

    def test_zstd(self):
        m = self._detect(ZSTD_BYTES)
        assert m and m.mime == "application/zstd"

    def test_lz4(self):
        m = self._detect(LZ4_BYTES)
        assert m and m.mime == "application/x-lz4"

    def test_tar(self):
        m = self._detect(TAR_BYTES)
        assert m and m.mime == "application/x-tar"

    # -- Edge cases --

    def test_empty_bytes(self):
        assert self.engine.detect(b"") is None

    def test_garbage_bytes(self):
        assert self.engine.detect(b"\x00" * 8192) is None

    def test_truncated_header_jpeg(self):
        # Only 2 bytes — not enough for 3-byte JPEG signature.
        assert self.engine.detect(b"\xff\xd8") is None

    def test_bytearray_input(self):
        m = self.engine.detect(bytearray(JPEG_BYTES))
        assert m and m.mime == "image/jpeg"


# ===========================================================================
# Security: Spoofing / polyglot attack tests
# ===========================================================================


class TestSpoofingPrevention:
    engine = MagicEngine()

    def test_jpeg_extension_png_content(self):
        """A PNG file renamed to .jpg must be detected as PNG, not JPEG."""
        m = self.engine.detect(PNG_BYTES)
        assert m and m.mime == "image/png"

    def test_pdf_with_null_prefix(self):
        """Null bytes prepended should prevent PDF detection."""
        data = b"\x00\x00" + PDF_BYTES
        m = self.engine.detect(data)
        assert m is None or m.mime != "application/pdf"

    def test_zip_disguised_as_jpeg(self):
        """ZIP header must not be detected as JPEG even if named .jpg."""
        m = self.engine.detect(ZIP_BYTES)
        assert m and m.mime != "image/jpeg"

    def test_oledb_not_detected_as_zip(self):
        """OLE2/CFB header should not match ZIP."""
        m = self.engine.detect(OLE2_BYTES)
        assert m and m.mime in {
            "application/msword",
            "application/vnd.ms-excel",
            "application/vnd.ms-powerpoint",
        }

    def test_malformed_odf_zip_rejected(self):
        """
        A ZIP that looks like ODF but has the wrong mimetype entry must not
        match any ODF MIME type.
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("mimetype", "application/x-bad-type")
            zf.writestr("content.xml", b"")
        data = buf.getvalue()
        m = self.engine.detect(data)
        # Should match generic ZIP, not any ODF type.
        assert m is None or "oasis" not in m.mime

    def test_docx_must_have_word_directory(self):
        """A ZIP without word/ entries must not be detected as DOCX."""
        data = _make_zip_with_entries("notword/document.xml")
        m = self.engine.detect(data)
        # Should match ZIP (or similar), not DOCX.
        assert m is None or "wordprocessingml" not in m.mime

    def test_mpeg_frame_sync_reserved_version_rejected(self):
        """MPEG frame with reserved version bits (01) must not match MP3."""
        # Byte 1: 0b11101??? — sync OK, version=01 (reserved).
        data = b"\xff\xea" + b"\x00" * 30
        m = MagicEngine().detect(data)
        # Should not be classified as audio/mpeg via the raw-frame path.
        if m:
            assert m.mime != "audio/mpeg"

    def test_mpeg_frame_sync_reserved_layer_rejected(self):
        """MPEG frame with reserved layer bits (00) must not match MP3."""
        # Byte 1 layout: 1110_VVLL_P (sync=111, version=10 MPEG2, layer=00 reserved, padding=0)
        # 0b11100001 = 0xE1 → version=00 (MPEG 2.5), layer=00 (reserved).
        # sync word OK (0xFF 0xE?), but layer bits are reserved.
        data = (
            b"\xff\xe0" + b"\x00" * 30
        )  # layer=00 (reserved) → _is_mp3_frame returns False
        m = MagicEngine().detect(data)
        if m:
            assert m.mime != "audio/mpeg"


# ===========================================================================
# Django validator integration tests
# ===========================================================================


class TestDeepSignatureValidator:
    """Integration tests for the Django-compatible validator class."""

    def _make(self, data: bytes, size: int | None = None):
        return _make_real_file(data, size)

    def test_valid_jpeg_passes(self):
        v = DeepSignatureValidator(["image/jpeg"])
        v(self._make(JPEG_BYTES))  # Must not raise.

    def test_valid_png_passes(self):
        v = DeepSignatureValidator(["image/jpeg", "image/png"])
        v(self._make(PNG_BYTES))

    def test_invalid_type_raises(self):
        v = DeepSignatureValidator(["image/jpeg"])
        with pytest.raises(ValidationError) as exc_info:
            v(self._make(PNG_BYTES))
        err = exc_info.value
        assert err.code == "invalid_type"

    def test_unknown_type_raises(self):
        v = DeepSignatureValidator(["image/jpeg"])
        with pytest.raises(ValidationError) as exc_info:
            v(self._make(b"\x00" * 64))
        assert exc_info.value.code == "unknown_type"

    def test_file_too_large_raises(self):
        v = DeepSignatureValidator(["image/jpeg"], max_size=100)
        with pytest.raises(ValidationError) as exc_info:
            # Report a size larger than the limit via the mock.
            f = self._make(JPEG_BYTES, size=200)
            v(f)
        assert exc_info.value.code == "file_too_large"

    def test_spec_size_limit_enforced_when_no_override(self):
        """Spec-level size limit must fire when no caller max_size is given."""
        # image/jpeg spec max_size is 1.5 MB; simulate a 2 MB file.
        v = DeepSignatureValidator(["image/jpeg"])
        f = self._make(JPEG_BYTES, size=2 * 1024 * 1024)
        with pytest.raises(ValidationError) as exc_info:
            v(f)
        assert exc_info.value.code == "file_too_large"

    def test_caller_max_size_overrides_spec(self):
        """Caller-supplied max_size=0 disables size checking."""
        v = DeepSignatureValidator(["image/jpeg"], max_size=0)
        # A JPEG well above the spec limit should pass when size-check disabled.
        f = self._make(JPEG_BYTES, size=50 * 1024 * 1024)
        v(f)  # Must not raise.

    def test_file_pointer_restored_on_success(self):
        """File pointer must be back at 0 after a successful validation."""
        v = DeepSignatureValidator(["image/jpeg"])
        buf = io.BytesIO(JPEG_BYTES)

        class FakeFile:
            size = len(JPEG_BYTES)
            name = "test.jpg"
            _buf = buf

            def read(self, n=-1):
                return buf.read(n)

            def seek(self, p, w=0):
                return buf.seek(p, w)

            def tell(self):
                return buf.tell()

        f = FakeFile()
        v(f)
        assert buf.tell() == 0

    def test_file_pointer_restored_on_failure(self):
        """File pointer must still be 0 even when validation raises."""
        v = DeepSignatureValidator(["image/jpeg"])
        buf = io.BytesIO(PNG_BYTES)

        class FakeFile:
            size = len(PNG_BYTES)
            name = "test.png"
            _buf = buf

            def read(self, n=-1):
                return buf.read(n)

            def seek(self, p, w=0):
                return buf.seek(p, w)

            def tell(self):
                return buf.tell()

        f = FakeFile()
        with pytest.raises(ValidationError):
            v(f)
        assert buf.tell() == 0

    def test_custom_error_message(self):
        v = DeepSignatureValidator(
            ["image/jpeg"],
            error_messages={"invalid_type": "Custom error: %(detected_mime)s"},
        )
        with pytest.raises(ValidationError) as exc_info:
            v(self._make(PNG_BYTES))
        assert "Custom error:" in str(exc_info.value.message)

    def test_equality_same_mimetypes(self):
        v1 = DeepSignatureValidator(["image/jpeg", "image/png"])
        v2 = DeepSignatureValidator(["image/png", "image/jpeg"])
        assert v1 == v2

    def test_equality_different_mimetypes(self):
        v1 = DeepSignatureValidator(["image/jpeg"])
        v2 = DeepSignatureValidator(["image/png"])
        assert v1 != v2

    def test_equality_different_max_size(self):
        v1 = DeepSignatureValidator(["image/jpeg"], max_size=100)
        v2 = DeepSignatureValidator(["image/jpeg"], max_size=200)
        assert v1 != v2

    def test_repr(self):
        v = DeepSignatureValidator(["image/jpeg"])
        assert "DeepSignatureValidator" in repr(v)
        assert "image/jpeg" in repr(v)


# ===========================================================================
# Preset validator smoke tests
# ===========================================================================


class TestPresets:
    def _make(self, data: bytes):
        return _make_real_file(data)

    def test_image_preset_accepts_jpeg(self):
        validate_image_file(self._make(JPEG_BYTES))

    def test_image_preset_accepts_png(self):
        validate_image_file(self._make(PNG_BYTES))

    def test_image_preset_accepts_webp(self):
        validate_image_file(self._make(WEBP_BYTES))

    def test_image_preset_rejects_pdf(self):
        with pytest.raises(ValidationError):
            validate_image_file(self._make(PDF_BYTES))

    def test_video_preset_accepts_mp4(self):
        validate_video_file(self._make(_make_mp4(b"isom")))

    def test_video_preset_accepts_webm(self):
        validate_video_file(self._make(WEBM_BYTES))

    def test_video_preset_rejects_mp3(self):
        with pytest.raises(ValidationError):
            validate_video_file(self._make(ID3_MP3))

    def test_audio_preset_accepts_mp3(self):
        validate_audio_file(self._make(ID3_MP3))

    def test_audio_preset_accepts_flac(self):
        validate_audio_file(self._make(FLAC_BYTES))

    def test_audio_preset_accepts_wav(self):
        validate_audio_file(self._make(WAV_BYTES))

    def test_audio_preset_rejects_jpeg(self):
        with pytest.raises(ValidationError):
            validate_audio_file(self._make(JPEG_BYTES))

    def test_document_preset_accepts_pdf(self):
        validate_document_file(self._make(PDF_BYTES))

    def test_document_preset_accepts_docx(self):
        data = _make_zip_with_entries("word/document.xml")
        validate_document_file(self._make(data))

    def test_document_preset_accepts_xlsx(self):
        data = _make_zip_with_entries("xl/workbook.xml")
        validate_document_file(self._make(data))

    def test_document_preset_accepts_pptx(self):
        data = _make_zip_with_entries("ppt/presentation.xml")
        validate_document_file(self._make(data))

    def test_document_preset_accepts_odt(self):
        validate_document_file(self._make(_make_odf("text")))

    def test_document_preset_accepts_ods(self):
        validate_document_file(self._make(_make_odf("spreadsheet")))

    def test_document_preset_accepts_odp(self):
        validate_document_file(self._make(_make_odf("presentation")))

    def test_document_preset_rejects_zip(self):
        """Plain ZIP (no Office structure) must be rejected by document preset."""
        data = _make_zip_with_entries("random_file.txt")
        with pytest.raises(ValidationError):
            validate_document_file(self._make(data))

    def test_archive_preset_accepts_zip(self):
        validate_archive_file(self._make(ZIP_BYTES))

    def test_archive_preset_accepts_7z(self):
        validate_archive_file(self._make(SEVENZIP_BYTES))

    def test_archive_preset_accepts_rar5(self):
        validate_archive_file(self._make(RAR_V5))

    def test_archive_preset_accepts_gzip(self):
        validate_archive_file(self._make(GZIP_BYTES))

    def test_archive_preset_accepts_xz(self):
        validate_archive_file(self._make(XZ_BYTES))

    def test_archive_preset_accepts_zstd(self):
        validate_archive_file(self._make(ZSTD_BYTES))

    def test_archive_preset_accepts_lz4(self):
        validate_archive_file(self._make(LZ4_BYTES))

    def test_archive_preset_rejects_jpeg(self):
        with pytest.raises(ValidationError):
            validate_archive_file(self._make(JPEG_BYTES))


# ===========================================================================
# Registry integrity checks
# ===========================================================================


class TestRegistryIntegrity:
    def test_all_specs_have_rules(self):
        """Every SignatureSpec must have at least one rule."""
        for spec in REGISTRY:
            assert len(spec.rules) >= 1, f"{spec.mime} ({spec.label}) has no rules"

    def test_all_specs_have_positive_max_size(self):
        """Every SignatureSpec must define a positive max_size."""
        for spec in REGISTRY:
            assert spec.max_size > 0, f"{spec.mime} ({spec.label}) has max_size <= 0"

    def test_no_duplicate_exact_specs(self):
        """No two specs should have identical (mime, rules) pairs."""
        seen: set[tuple] = set()
        for spec in REGISTRY:
            key = (spec.mime, tuple(spec.rules))
            assert key not in seen, f"Duplicate spec: {spec.mime} ({spec.label})"
            seen.add(key)

    def test_all_mimes_are_strings(self):
        for spec in REGISTRY:
            assert isinstance(spec.mime, str) and "/" in spec.mime, (
                f"Invalid MIME type: {spec.mime!r}"
            )
