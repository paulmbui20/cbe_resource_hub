"""
Django File Validators — Deep Magic-Byte Signature Engine
==========================================================

A pure-Python, zero-dependency file type validation library for Django 6+
(Python 3.12+) that performs cryptographically-sound file signature (magic
byte) validation without relying on libmagic or any C extensions.

Usage
-----
from validators import (
    validate_image_file,
    validate_video_file,
    validate_document_file,
    validate_audio_file,
    validate_archive_file,
    DeepSignatureValidator,
)

# As a model field validator:
avatar = models.FileField(
    upload_to="avatars/",
    validators=[validate_image_file],
)

# As a custom validator with explicit MIME types:
resume = models.FileField(
    upload_to="resumes/",
    validators=[DeepSignatureValidator(allowed_mimetypes={"application/pdf"})],
)
"""

from .core import DeepSignatureValidator, MagicEngine, SignatureMatch
from .presets import (
    validate_archive_file,
    validate_audio_file,
    validate_document_file,
    validate_image_file,
    validate_video_file,
)
from .signatures import REGISTRY

__all__ = [
    # Core engine
    "MagicEngine",
    "DeepSignatureValidator",
    "SignatureMatch",
    # Convenience preset validators
    "validate_image_file",
    "validate_video_file",
    "validate_document_file",
    "validate_audio_file",
    "validate_archive_file",
    # Full signature registry (for introspection / custom builds)
    "REGISTRY",
]
