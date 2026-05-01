"""
validators/presets.py
=====================

Ready-to-use ``DeepSignatureValidator`` instances for common upload scenarios.

Import any of these directly into a model ``validators=`` list without
needing to specify MIME types manually.

Each preset validator:

* Accepts a curated set of MIME types relevant to the category.
* Uses the per-``SignatureSpec`` size limits defined in ``signatures.py``
  (so e.g. images are capped at 1.5 MB and videos at 500 MB automatically).
* Can be overridden with a custom ``max_size`` by creating your own
  ``DeepSignatureValidator`` instance instead.

Available presets
-----------------
validate_image_file
    JPEG, PNG, GIF, WebP, BMP, TIFF, AVIF, HEIC, SVG, ICO.

validate_video_file
    MP4, QuickTime/MOV, WebM, OGG video, AVI, Matroska/MKV, FLV.

validate_audio_file
    MP3, AAC, M4A, OGG audio, FLAC, WAV, AIFF, Opus, WMA, AMR.

validate_document_file
    PDF, DOCX, XLSX, PPTX, ODT, ODS, ODP, legacy DOC/XLS/PPT, RTF, EPUB.

validate_archive_file
    ZIP, 7-Zip, RAR, TAR, GZip, BZip2, XZ, Zstandard, LZ4.
"""

from .core import DeepSignatureValidator

# ---------------------------------------------------------------------------
# Image formats
# ---------------------------------------------------------------------------

validate_image_file = DeepSignatureValidator(
    allowed_mimetypes=[
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/bmp",
        "image/tiff",
        "image/avif",
        "image/heic",
        "image/svg+xml",
        "image/x-icon",
    ],
)
"""
Validates that the upload is a recognised image format.

Accepted formats: JPEG, PNG, GIF, WebP, BMP, TIFF, AVIF, HEIC/HEIF,
SVG, and ICO.

Size limits are determined per-format by the registry (typically 1.5 MB
for raster images, 20 MB for TIFF).
"""

# ---------------------------------------------------------------------------
# Video formats
# ---------------------------------------------------------------------------

validate_video_file = DeepSignatureValidator(
    allowed_mimetypes=[
        "video/mp4",
        "video/quicktime",
        "video/webm",
        "video/ogg",
        "video/x-msvideo",
        "video/x-matroska",
        "video/x-flv",
    ],
)
"""
Validates that the upload is a recognised video container.

Accepted formats: MP4, QuickTime/MOV, WebM, OGG video, AVI,
Matroska/MKV, and FLV.  All formats are capped at 500 MB.
"""

# ---------------------------------------------------------------------------
# Audio formats
# ---------------------------------------------------------------------------

validate_audio_file = DeepSignatureValidator(
    allowed_mimetypes=[
        "audio/mpeg",  # MP3
        "audio/aac",  # AAC (ADTS)
        "audio/mp4",  # M4A / AAC-in-MP4
        "audio/ogg",  # Vorbis / Theora in OGG
        "audio/opus",  # Opus in OGG
        "audio/flac",  # FLAC
        "audio/wav",  # PCM WAV
        "audio/aiff",  # AIFF / AIFC
        "audio/x-ms-wma",  # WMA
        "audio/amr",  # AMR narrowband
    ],
)
"""
Validates that the upload is a recognised audio format.

Accepted formats: MP3 (ID3v1/v2 and raw MPEG frame), AAC (ADTS),
M4A, OGG Vorbis, Opus, FLAC, WAV, AIFF/AIFC, WMA, and AMR.
"""

# ---------------------------------------------------------------------------
# Document formats
# ---------------------------------------------------------------------------

validate_document_file = DeepSignatureValidator(
    allowed_mimetypes=[
        "application/pdf",
        # Office Open XML (modern Microsoft Office)
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        # OpenDocument Format (LibreOffice / OpenOffice / Google Docs export)
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.presentation",
        # Legacy Microsoft Office (OLE2 compound document)
        "application/msword",
        "application/vnd.ms-excel",
        "application/vnd.ms-powerpoint",
        # Other
        "application/rtf",
        "application/epub+zip",
    ],
)
"""
Validates that the upload is a recognised document format.

Accepted formats:
* PDF
* DOCX / XLSX / PPTX (Office Open XML — Word, Excel, PowerPoint)
* ODT / ODS / ODP (OpenDocument — LibreOffice, OpenOffice, Google Docs)
* DOC / XLS / PPT (legacy Microsoft Office — OLE2)
* RTF
* EPUB
"""

# ---------------------------------------------------------------------------
# Archive / compressed formats
# ---------------------------------------------------------------------------

validate_archive_file = DeepSignatureValidator(
    allowed_mimetypes=[
        "application/zip",
        "application/x-7z-compressed",
        "application/x-rar-compressed",
        "application/x-tar",
        "application/gzip",
        "application/x-bzip2",
        "application/x-xz",
        "application/zstd",
        "application/x-lz4",
    ],
)
"""
Validates that the upload is a recognised archive or compressed format.

Accepted formats: ZIP, 7-Zip, RAR (v1.5 and v5), TAR (POSIX ustar),
GZip (.gz / .tar.gz), BZip2 (.bz2 / .tar.bz2), XZ (.xz / .tar.xz),
Zstandard (.zst), and LZ4 (.lz4).  All formats are capped at 500 MB.
"""
