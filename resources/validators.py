# resources/validators.py

from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE = 1.5 * 1024 * 1024  # 1.5MB in bytes
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB in bytes
ALLOWED_IMAGE_MIME_TYPES = ["image/png", "image/jpeg", "image/jpg"]
ALLOWED_VIDEO_MIME_TYPES = ["video/mp4", "video/webm", "video/ogg", "video/quicktime"]

# File signature definitions
FILE_SIGNATURES = {
    "image/jpeg": [
        (0, b"\xff\xd8\xff\xe0"),  # JPEG/JFIF
        (0, b"\xff\xd8\xff\xe1"),  # JPEG/Exif
        (0, b"\xff\xd8\xff\xe8"),  # JPEG/SPIFF
        (0, b"\xff\xd8\xff\xdb"),  # JPEG with quantization table
        (0, b"\xff\xd8\xff\xee"),  # JPEG with Adobe marker
    ],
    "image/jpg": [
        (0, b"\xff\xd8\xff\xe0"),  # JPG/JFIF (technically same as JPEG)
        (0, b"\xff\xd8\xff\xe1"),  # JPG/Exif (technically same as JPEG)
        (0, b"\xff\xd8\xff\xe8"),  # JPG/SPIFF (technically same as JPEG)
        (0, b"\xff\xd8\xff\xdb"),  # JPG with quantization table
        (0, b"\xff\xd8\xff\xee"),  # JPG with Adobe marker
    ],
    "image/png": [
        (0, b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"),  # PNG
    ],
    "video/mp4": [
        (4, b"ftyp"),  # MP4 container (generic)
        (4, b"ftypmp4"),  # Most common MP4
        (4, b"ftypisom"),  # ISO Base Media
        (4, b"ftypMSNV"),  # Sony MP4
    ],
    "video/webm": [
        (0, b"\x1a\x45\xdf\xa3"),  # WebM EBML header
    ],
    "video/ogg": [
        (0, b"OggS"),  # OGG container format
    ],
    "video/quicktime": [
        (4, b"ftypqt"),  # QuickTime container
        (4, b"ftypmoov"),  # Another QuickTime marker
    ],
}


def get_mime_type(file_data):
    """
    Determine the MIME type based on file signatures (magic bytes).

    Args:
        file_data: The binary data from the beginning of the file (at least 32 bytes).

    Returns:
        str: The detected MIME type, or None if not recognized.
    """
    if not file_data:
        return None

    for mime_type, signatures in FILE_SIGNATURES.items():
        for offset, signature in signatures:
            if len(file_data) >= offset + len(signature):
                if file_data[offset: offset + len(signature)] == signature:
                    return mime_type
    return None


def validate_image_file_magic(value):
    """
    Validates that the uploaded file is a PNG or JPEG/JPG image and does not exceed 1.5MB using magic bytes.

    Args:
        value: The uploaded file object (an instance of UploadedFile).

    Raises:
        ValidationError: If the file size exceeds 1.5MB or the file type is not PNG/JPEG/JPG.
    """
    # Check file size
    if value.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f"Image file size must be no more than 1.5MB. Current size is {value.size / (1024 * 1024):.2f}MB."
        )

    # Read sufficient bytes for magic byte detection
    try:
        header_bytes = value.read(32)
        mime = get_mime_type(header_bytes)
    except Exception as e:
        raise ValidationError(f"Error reading file: {str(e)}")
    finally:
        # Always seek back to beginning
        if hasattr(value, 'seek'):
            try:
                value.seek(0)
            except:
                pass

    if mime not in ALLOWED_IMAGE_MIME_TYPES:
        detected = mime if mime else "unknown"
        raise ValidationError(
            f"Unsupported image file type: {detected}. Only PNG and JPEG/JPG are allowed."
        )


def validate_video_file_magic(value):
    """
    Validates that the uploaded file is a supported video format (MP4, WebM, OGG, QuickTime)
    and does not exceed 50MB using magic bytes.

    Args:
        value: The uploaded file object (an instance of UploadedFile).

    Raises:
        ValidationError: If the file size exceeds 50MB or the file type is not a supported video format.
    """
    # Check file size
    if value.size > MAX_VIDEO_SIZE:
        raise ValidationError(
            f"Video file size must be no more than 50MB. Current size is {value.size / (1024 * 1024):.2f}MB."
        )

    # Read sufficient bytes for magic byte detection
    try:
        header_bytes = value.read(32)
        mime = get_mime_type(header_bytes)
    except Exception as e:
        raise ValidationError(f"Error reading file: {str(e)}")
    finally:
        # Always seek back to beginning
        if hasattr(value, 'seek'):
            try:
                value.seek(0)
            except:
                pass

    if mime not in ALLOWED_VIDEO_MIME_TYPES:
        detected = mime if mime else "unknown"
        raise ValidationError(
            f"Unsupported video file type: {detected}. Only MP4, WebM, OGG, and QuickTime are allowed."
        )
