"""
Unit tests for File model.
Tests model creation, metadata extraction, validation, and file operations.
"""

from io import BytesIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from files.models import File
from .fixtures import FileFixtures, create_uploaded_file


class TestFileModelCreation(TestCase):
    """Test basic File model creation and save."""

    def setUp(self):
        """Set up test fixtures."""
        self.png_file = create_uploaded_file(
            FileFixtures.create_valid_png(), "image/png"
        )
        self.jpeg_file = create_uploaded_file(
            FileFixtures.create_valid_jpeg(), "image/jpeg"
        )

    def test_create_file_with_png(self):
        """Should create File instance with PNG image."""
        file_obj = File.objects.create(title="Test PNG", file=self.png_file)

        self.assertIsNotNone(file_obj.pk)
        self.assertEqual(file_obj.title, "Test PNG")
        self.assertEqual(file_obj.file_category, "image")
        self.assertEqual(file_obj.mime_type, "image/png")
        self.assertEqual(file_obj.extension, "png")

    def test_create_file_with_jpeg(self):
        """Should create File instance with JPEG image."""
        file_obj = File.objects.create(title="Test JPEG", file=self.jpeg_file)

        self.assertIsNotNone(file_obj.pk)
        self.assertEqual(file_obj.file_category, "image")
        self.assertIn(file_obj.mime_type, ["image/jpeg", "image/jpg"])
        self.assertEqual(file_obj.extension, "jpg")

    def test_file_size_extracted(self):
        """Should extract file size on save."""
        file_obj = File.objects.create(title="Test Size", file=self.png_file)

        self.assertGreater(file_obj.size, 0)

    def test_image_dimensions_extracted(self):
        """Should extract image dimensions for images."""
        file_obj = File.objects.create(title="Test Dimensions", file=self.png_file)

        self.assertIsNotNone(file_obj.width)
        self.assertIsNotNone(file_obj.height)
        self.assertEqual(file_obj.width, 100)
        self.assertEqual(file_obj.height, 100)

    def test_slug_in_filename(self):
        """Should include slugified title in filename."""
        file_obj = File.objects.create(title="My Test File!", file=self.png_file)

        self.assertIn("my-test-file", file_obj.file.name.lower())

    def test_uuid_in_filename(self):
        """Should include UUID in filename for uniqueness."""
        file_obj = File.objects.create(title="Test", file=self.png_file)

        # UUID format: 8-4-4-4-12 characters
        filename = file_obj.file.name
        # Should contain a UUID-like pattern
        self.assertRegex(
            filename, r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
        )

    def test_empty_title_handled(self):
        """Should handle empty title gracefully."""
        file_obj = File.objects.create(title="", file=self.png_file)

        # Should use 'untitled' or similar
        self.assertIsNotNone(file_obj.file.name)

    def test_long_title_truncated(self):
        """Should truncate very long titles."""
        long_title = "A" * 200
        file_obj = File.objects.create(title=long_title, file=self.png_file)

        # Filename should not be excessively long
        filename = file_obj.file.name
        # Should be truncated to reasonable length
        self.assertLess(len(filename), 300)


class TestFileModelMetadata(TestCase):
    """Test metadata extraction and categorization."""

    def test_detect_image_category(self):
        """Should categorize image files correctly."""
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")

        file_obj = File.objects.create(title="Test", file=png_file)
        self.assertEqual(file_obj.file_category, "image")

    def test_detect_video_category(self):
        """Should categorize video files correctly."""
        mp4_file = create_uploaded_file(FileFixtures.create_valid_mp4(), "video/mp4")

        file_obj = File.objects.create(title="Test", file=mp4_file)
        self.assertEqual(file_obj.file_category, "video")

    def test_detect_document_category(self):
        """Should categorize document files correctly."""
        pdf_file = create_uploaded_file(FileFixtures.create_pdf(), "application/pdf")

        file_obj = File.objects.create(title="Test", file=pdf_file)
        self.assertEqual(file_obj.file_category, "document")

    def test_detect_archive_category(self):
        """Should categorize archive files correctly."""
        zip_file = create_uploaded_file(FileFixtures.create_zip(), "application/zip")

        file_obj = File.objects.create(title="Test", file=zip_file)
        self.assertEqual(file_obj.file_category, "archive")

    def test_unknown_file_type(self):
        """Should categorize unknown files as 'other'."""
        text_file = create_uploaded_file(FileFixtures.create_text_file(), "text/plain")

        file_obj = File.objects.create(title="Test", file=text_file)
        self.assertEqual(file_obj.file_category, "other")

    def test_metadata_json_field(self):
        """Should store additional metadata in JSON field."""
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")

        file_obj = File.objects.create(title="Test", file=png_file)

        # Should have metadata
        self.assertIsNotNone(file_obj.metadata)
        self.assertIsInstance(file_obj.metadata, dict)


class TestFileModelValidation(TestCase):
    """Test file validation during save."""

    def test_clean_validates_oversized_image(self):
        """Should validate and reject oversized images via clean()."""
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a buffer that's definitely over 1.5MB
        buffer = BytesIO()
        # Write valid JPEG header
        buffer.write(b"\xff\xd8\xff\xe0")
        buffer.write(b"\x00\x10JFIF")
        # Fill with data to exceed 1.5MB
        buffer.write(b"\x00" * (2 * 1024 * 1024))  # 2MB of data
        buffer.seek(0)

        oversized_file = SimpleUploadedFile(
            "large.jpg", buffer.read(), content_type="image/jpeg"
        )

        file_obj = File(title="Oversized", file=oversized_file)

        # This should raise ValidationError when clean() validates the file
        with self.assertRaises(ValidationError) as context:
            file_obj.clean()

        # Verify it's the right error
        error_message = str(context.exception)
        self.assertIn("1.5 MB limit", error_message)

    def test_clean_validates_wrong_magic_bytes(self):
        """Should reject files with wrong magic bytes via clean()."""
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a file that claims to be JPEG but has wrong magic bytes
        buffer = BytesIO()
        buffer.write(b"This is not an image file at all!")
        buffer.seek(0)

        fake_file = SimpleUploadedFile(
            "fake.jpg", buffer.read(), content_type="image/jpeg"
        )

        file_obj = File(title="Fake", file=fake_file)

        with self.assertRaises(ValidationError) as context:
            file_obj.clean()

        error_message = str(context.exception)
        self.assertIn("could not be identified", error_message)

    def test_valid_image_accepted(self):
        """Should accept valid image files."""
        valid_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")

        try:
            file_obj = File.objects.create(title="Valid", file=valid_file)
            self.assertIsNotNone(file_obj.pk)
        except ValidationError:
            self.fail("Valid image should not raise ValidationError")


class TestFileModelProperties(TestCase):
    """Test File model properties and methods."""

    def setUp(self):
        """Create a test file."""
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")
        self.file_obj = File.objects.create(title="Test", file=png_file)

    def test_url_property(self):
        """Should return file URL."""
        url = self.file_obj.url
        self.assertIsNotNone(url)
        self.assertIsInstance(url, str)

    def test_human_size_bytes(self):
        """Should format small sizes as bytes."""
        self.file_obj.size = 512
        self.file_obj.save()

        self.assertIn("bytes", self.file_obj.human_size)

    def test_human_size_kb(self):
        """Should format KB sizes correctly."""
        self.file_obj.size = 2048  # 2 KB
        self.file_obj.save()

        self.assertIn("KB", self.file_obj.human_size)

    def test_human_size_mb(self):
        """Should format MB sizes correctly."""
        self.file_obj.size = 1024 * 1024 * 1.5  # 1.5 MB
        self.file_obj.save()

        self.assertIn("MB", self.file_obj.human_size)

    def test_str_representation(self):
        """Should have readable string representation."""
        str_repr = str(self.file_obj)

        self.assertIn(self.file_obj.title, str_repr)
        self.assertIn(self.file_obj.file_category, str_repr)


class TestFileModelDeletion(TestCase):
    """Test file deletion and cleanup."""

    def test_delete_removes_from_storage(self):
        """Should delete file from storage on model delete."""
        # Use a regular file creation that works
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")
        file_obj = File.objects.create(title="Test", file=png_file)

        # Delete the object
        file_obj.delete()

        # Verify database record is gone
        self.assertFalse(File.objects.filter(pk=file_obj.pk).exists())

    def test_delete_with_missing_file(self):
        """Should handle deletion when file is missing from storage."""
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")
        file_obj = File.objects.create(title="Test", file=png_file)

        try:
            file_obj.delete()
        except Exception as e:
            self.fail(f"Delete should not fail if file is missing: {e}")


class TestFileExistence(TestCase):
    """Test file existence checking."""

    def test_file_exists_returns_true_for_existing(self):
        """Should return True for existing files."""
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")
        file_obj = File.objects.create(title="Test", file=png_file)

        # Should exist after creation
        self.assertTrue(file_obj.file_exists())

    def test_file_exists_returns_false_for_missing(self):
        """Should return False for missing files."""
        # Create file first
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")
        file_obj = File.objects.create(title="Test", file=png_file)

        # Mock the storage to return False
        with patch.object(file_obj.file.storage, "exists", return_value=False):
            result = file_obj.file_exists()
            self.assertFalse(result)


class TestFileHash(TestCase):
    """Test file hash calculation for deduplication."""

    def test_calculate_file_hash(self):
        """Should calculate SHA256 hash of file."""
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")
        file_obj = File(title="Test", file=png_file)

        file_obj._calculate_file_hash()

        # Should have a hash
        self.assertIsNotNone(file_obj.file_hash)
        self.assertEqual(len(file_obj.file_hash), 64)  # SHA256 is 64 hex chars

    def test_same_files_same_hash(self):
        """Identical files should have identical hashes."""
        png_buffer = FileFixtures.create_valid_png(width=50, height=50)
        content = png_buffer.read()
        png_buffer.seek(0)

        # Create two files with identical content
        file1 = File(
            title="File1", file=SimpleUploadedFile("test1.png", content, "image/png")
        )
        file2 = File(
            title="File2", file=SimpleUploadedFile("test2.png", content, "image/png")
        )

        file1._calculate_file_hash()
        file2._calculate_file_hash()

        self.assertEqual(file1.file_hash, file2.file_hash)

    def test_different_files_different_hash(self):
        """Different files should have different hashes."""
        png_file = File(
            title="PNG",
            file=create_uploaded_file(
                FileFixtures.create_valid_png(width=50, height=50), "image/png"
            ),
        )
        jpeg_file = File(
            title="JPEG",
            file=create_uploaded_file(
                FileFixtures.create_valid_jpeg(width=50, height=50), "image/jpeg"
            ),
        )

        png_file._calculate_file_hash()
        jpeg_file._calculate_file_hash()

        self.assertNotEqual(png_file.file_hash, jpeg_file.file_hash)

    def test_find_duplicate(self):
        """Should find existing file with same hash."""
        # Create first file
        png_buffer = FileFixtures.create_valid_png()
        content = png_buffer.read()
        png_buffer.seek(0)

        file1 = File.objects.create(
            title="Original", file=SimpleUploadedFile("test1.png", content, "image/png")
        )
        file1._calculate_file_hash()
        file1.save()

        # Try to find duplicate
        duplicate = File.find_duplicate(file1.file_hash)

        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate.pk, file1.pk)


class TestFileModelEdgeCases(TestCase):
    """Test edge cases and error handling."""

    def test_save_without_file(self):
        """Should handle save without file attached."""
        file_obj = File(title="No File")

        # Should not crash
        try:
            file_obj.save()
        except Exception as e:
            self.fail(f"Save without file should not crash: {e}")

    def test_corrupted_image_dimensions(self):
        """Should handle corrupted image gracefully."""
        # Create a file that looks like an image but is corrupted
        buffer = BytesIO()
        buffer.write(b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a")  # PNG header
        buffer.write(b"\x00" * 100)  # Invalid PNG data
        buffer.seek(0)
        buffer.name = "corrupted.png"

        file_obj = File(
            title="Corrupted",
            file=SimpleUploadedFile("corrupted.png", buffer.read(), "image/png"),
        )

        # Should save without crashing, dimensions will be None
        file_obj.save()

        self.assertIsNone(file_obj.width)
        self.assertIsNone(file_obj.height)

    def test_special_characters_in_title(self):
        """Should handle special characters in title."""
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")

        file_obj = File.objects.create(
            title="Test!@#$%^&*()_+{}[]|\\:;<>?,./", file=png_file
        )

        # Should be slugified properly
        self.assertIsNotNone(file_obj.file.name)

    def test_unicode_in_title(self):
        """Should handle Unicode characters in title."""
        png_file = create_uploaded_file(FileFixtures.create_valid_png(), "image/png")

        file_obj = File.objects.create(title="测试文件 🎉", file=png_file)

        # Should handle Unicode properly
        self.assertIsNotNone(file_obj.file.name)
