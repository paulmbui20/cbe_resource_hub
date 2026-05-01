import hashlib
import logging
import mimetypes
import os
import sys
from io import BytesIO
from uuid import uuid4

from PIL import Image
from django.core.files.storage import storages
from django.db import models, transaction
from django.utils.text import slugify

from validators import (
    MagicEngine,
    validate_document_file,
    validate_video_file,
    validate_archive_file,
    validate_audio_file,
    validate_image_file,
)

logger = logging.getLogger(__name__)


def file_upload_path(instance, filename):
    """
    Generate upload path for files with collision prevention.
    """
    # Get extension safely
    ext = filename.split(".")[-1] if "." in filename else ""

    # Safely handle title (limit length and handle empty titles)
    safe_title = slugify(instance.title or "file")[:50] or "untitled"

    # Generate unique filename
    filename = f"{safe_title}-{uuid4()}.{ext}" if ext else f"{safe_title}-{uuid4()}"

    # Return path (category will be set before this is called)
    category = getattr(instance, "file_category", "other") or "other"
    return f"files/{category}/{filename}"


class PublicFilesStorageCallable:
    """
    Callable that returns the appropriate storage backend for files.
    This is evaluated at runtime, not at class definition time.
    """

    def __call__(self):
        from django.core.files.storage import FileSystemStorage

        # In tests, always use FileSystemStorage
        if "pytest" in sys.modules or "test" in sys.argv:
            return FileSystemStorage()

        try:
            return storages["public_files"]
        except (KeyError, AttributeError):
            # Fallback to default storage
            return storages["default"]

    def deconstruct(self):
        """
        Allow Django to serialize this for migrations.
        """
        return ("files.models.PublicFilesStorageCallable", [], {})


class File(models.Model):
    CATEGORY_CHOICES = (
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("document", "Document"),
        ("archive", "Archive"),
        ("other", "Other"),
    )

    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to=file_upload_path,
        storage=PublicFilesStorageCallable(),
        validators=[
            validate_document_file,
            validate_video_file,
            validate_archive_file,
            validate_audio_file,
            validate_image_file,
        ],
    )

    # Auto-detected fields
    mime_type = models.CharField(max_length=100, blank=True)
    extension = models.CharField(max_length=10, blank=True)
    file_category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="other"
    )

    # Size from storage (R2 safe)
    size = models.PositiveIntegerField(default=0)

    # Image-dimension metadata
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    # File hash for deduplication (optional but recommended)
    file_hash = models.CharField(max_length=64, blank=True, db_index=True)

    metadata = models.JSONField(default=dict, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["file_category", "-created"]),
            models.Index(fields=["mime_type"]),
            models.Index(fields=["-created"]),
        ]
        ordering = ["-created"]

    # -----------------------------
    # VALIDATION
    # -----------------------------
    def clean(self):
        """
        Run validation including magic-byte checks.
        This is called by ModelForms and DRF serializers automatically.
        """
        super().clean()

        if not self.file:
            return

        # Detect MIME type first if not already done
        if not self.mime_type:
            try:
                sample = self.file.read(32)
                if hasattr(self.file, "seek"):
                    self.file.seek(0)
                match = MagicEngine().detect(sample)
                self.mime_type = (
                    match.mime if match else None
                ) or mimetypes.guess_type(self.file.name)[0]
            except Exception as e:
                logger.warning(f"Could not detect MIME type: {e}")

        # Run magic-byte validators based on detected MIME type
        mime = self.mime_type or mimetypes.guess_type(self.file.name)[0]

        if mime:
            try:
                if mime.startswith("image"):
                    validate_image_file(self.file)
                elif mime.startswith("video"):
                    validate_video_file(self.file)
            except Exception as e:
                # Re-raise validation errors
                raise

    # -----------------------------
    # SAVE + METADATA EXTRACTION
    # -----------------------------
    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Save safely for cloud storage.
        Extract metadata from file.read() instead of file.path.
        Only saves once to avoid race conditions.
        """
        is_new = self.pk is None

        # Extract metadata only if file exists and hasn't been processed
        if self.file and (is_new or not self.mime_type):
            try:
                self._extract_metadata()
            except Exception as e:
                logger.error(
                    f"Error extracting metadata for {self.title}: {e}", exc_info=True
                )
                # Don't fail the save, but log the error

        # Validate on creation (for programmatic saves that bypass forms)
        if is_new:
            try:
                self.clean()
            except Exception as e:
                logger.error(f"Validation failed for {self.title}: {e}")
                raise

        # Single save operation
        super().save(*args, **kwargs)

    def _extract_metadata(self):
        """
        Extract all metadata from the file in one go.
        Handles R2/cloud storage safely without using file.path.
        """
        if not self.file:
            return

        try:
            # Read file head for magic byte detection (32 bytes is sufficient)
            sample = self.file.read(32)
            if hasattr(self.file, "seek"):
                self.file.seek(0)

            # Detect MIME type (prioritize magic bytes over extension)
            match = MagicEngine().detect(sample)
            detected_mime = match.mime if match else None
            guessed_mime = mimetypes.guess_type(self.file.name)[0]
            self.mime_type = detected_mime or guessed_mime or "application/octet-stream"

            # Extract extension safely
            ext = os.path.splitext(self.file.name)[1].lower()
            self.extension = ext.replace(".", "") if ext else ""

            # Get file size (R2-safe)
            self.size = self.file.size

            # Determine category
            self.file_category = self.detect_file_category()

            # Extract type-specific metadata
            if self.file_category == "image":
                self._extract_image_dimensions()

        except Exception as e:
            logger.error(f"Error in _extract_metadata: {e}", exc_info=True)
            raise

    # -----------------------------
    # CATEGORY DETECTION
    # -----------------------------
    def detect_file_category(self):
        """Determine file category based on MIME type."""
        mt = self.mime_type

        if not mt:
            return "other"

        mt_lower = mt.lower()

        if mt_lower.startswith("image"):
            return "image"
        if mt_lower.startswith("video"):
            return "video"
        if mt_lower.startswith("audio"):
            return "audio"
        if mt_lower in [
            "application/zip",
            "application/x-tar",
            "application/x-rar-compressed",
            "application/x-7z-compressed",
        ]:
            return "archive"
        if any(
            x in mt_lower
            for x in [
                "pdf",
                "word",
                "sheet",
                "document",
                "presentation",
                "msword",
                "ms-excel",
                "ms-powerpoint",
            ]
        ):
            return "document"

        return "other"

    # -----------------------------
    # IMAGE DIMENSIONS (cloud-safe)
    # -----------------------------
    def _extract_image_dimensions(self):
        """
        Extract image dimensions safely for cloud storage.
        Reads entire file into memory (safe for images under 1.5MB).
        """
        try:
            # Read entire file content
            img_bytes = self.file.read()

            # Seek back to beginning if possible
            if hasattr(self.file, "seek"):
                self.file.seek(0)

            # Open with PIL
            img = Image.open(BytesIO(img_bytes))
            self.width, self.height = img.size

            # Store additional metadata if needed
            if not self.metadata:
                self.metadata = {}
            self.metadata["format"] = img.format
            self.metadata["mode"] = img.mode

        except Exception as e:
            logger.warning(f"Could not extract image dimensions: {e}")
            self.width = None
            self.height = None

    # -----------------------------
    # FILE HASH (for deduplication)
    # -----------------------------
    def _calculate_file_hash(self):
        """
        Calculate SHA256 hash of file content for deduplication.
        Warning: This reads the entire file, which can be slow for large files.
        """
        if not self.file:
            return

        try:
            sha256 = hashlib.sha256()

            # Read file in chunks to avoid memory issues
            for chunk in self.file.chunks():
                sha256.update(chunk)

            self.file_hash = sha256.hexdigest()

            # Seek back to beginning
            if hasattr(self.file, "seek"):
                self.file.seek(0)

        except Exception as e:
            logger.warning(f"Could not calculate file hash: {e}")
            self.file_hash = ""

    # -----------------------------
    # FILE EXISTENCE CHECK
    # -----------------------------
    def file_exists(self):
        """
        Check if file actually exists in storage.
        Useful for detecting orphaned records.
        """
        if not self.file:
            return False

        try:
            return self.file.storage.exists(self.file.name)
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False

    # -----------------------------
    # PROPERTIES
    # -----------------------------
    @property
    def url(self):
        """Get file URL safely."""
        if self.file:
            try:
                return self.file.url
            except Exception as e:
                logger.error(f"Error getting file URL: {e}")
                return None
        return None

    @property
    def human_size(self):
        """Return human-readable file size."""
        size = self.size
        for unit in ["bytes", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def __str__(self):
        return f"{self.title} ({self.file_category}/{self.mime_type})"

    # -----------------------------
    # DELETE (R2 SAFE)
    # -----------------------------
    def delete(self, *args, **kwargs):
        """
        Delete file from storage and database.
        Attempts to delete from storage first to avoid orphaned files.
        """
        if self.file:
            storage = self.file.storage
            name = self.file.name

            try:
                # Try to delete from storage first
                if storage.exists(name):
                    storage.delete(name)
                    logger.info(f"Deleted file from storage: {name}")
            except Exception as e:
                # Log error but continue with DB deletion
                # Orphaned files are better than broken database records
                logger.error(
                    f"Failed to delete file from storage {name}: {e}", exc_info=True
                )

        # Delete database record
        super().delete(*args, **kwargs)

    # -----------------------------
    # UTILITY METHODS
    # -----------------------------
    @classmethod
    def find_duplicate(cls, file_hash):
        """
        Find existing file with same hash (for deduplication).
        Returns existing File instance or None.
        """
        if not file_hash:
            return None

        try:
            return cls.objects.filter(file_hash=file_hash).first()
        except Exception:
            return None

    def get_absolute_url(self):
        """Return admin URL for this file."""
        from django.urls import reverse

        return reverse("admin:files_file_change", args=[self.pk])
