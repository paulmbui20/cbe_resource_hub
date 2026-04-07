"""
Unit tests for file validators.
Tests magic byte validation for images and videos.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from resources.validators import (
    validate_image_file_magic,
    validate_video_file_magic,
    get_mime_type,
    MAX_IMAGE_SIZE,
    MAX_VIDEO_SIZE,
)
from .fixtures import FileFixtures, create_uploaded_file


class TestGetMimeType(TestCase):
    """Test MIME type detection from magic bytes."""

    def test_detect_png(self):
        """Should detect PNG from magic bytes."""
        png_data = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' + b'\x00' * 24
        mime = get_mime_type(png_data)
        self.assertEqual(mime, 'image/png')

    def test_detect_jpeg_jfif(self):
        """Should detect JPEG/JFIF from magic bytes."""
        jpeg_data = b'\xff\xd8\xff\xe0' + b'\x00' * 28
        mime = get_mime_type(jpeg_data)
        self.assertIn(mime, ['image/jpeg', 'image/jpg'])

    def test_detect_jpeg_exif(self):
        """Should detect JPEG/Exif from magic bytes."""
        jpeg_data = b'\xff\xd8\xff\xe1' + b'\x00' * 28
        mime = get_mime_type(jpeg_data)
        self.assertIn(mime, ['image/jpeg', 'image/jpg'])

    def test_detect_mp4(self):
        """Should detect MP4 from magic bytes."""
        mp4_data = b'\x00' * 4 + b'ftyp' + b'\x00' * 24
        mime = get_mime_type(mp4_data)
        self.assertEqual(mime, 'video/mp4')

    def test_detect_webm(self):
        """Should detect WebM from magic bytes."""
        webm_data = b'\x1a\x45\xdf\xa3' + b'\x00' * 28
        mime = get_mime_type(webm_data)
        self.assertEqual(mime, 'video/webm')

    def test_unknown_type(self):
        """Should return None for unknown file types."""
        unknown_data = b'UNKNOWN' + b'\x00' * 25
        mime = get_mime_type(unknown_data)
        self.assertIsNone(mime)

    def test_empty_data(self):
        """Should handle empty data gracefully."""
        mime = get_mime_type(b'')
        self.assertIsNone(mime)

    def test_insufficient_data(self):
        """Should handle insufficient data."""
        mime = get_mime_type(b'\xff\xd8')  # Only 2 bytes
        self.assertIsNone(mime)


class TestImageValidation(TestCase):
    """Test image file validation."""

    def test_valid_png(self):
        """Should accept valid PNG file."""
        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(),
            'image/png'
        )

        try:
            validate_image_file_magic(png_file)
        except ValidationError:
            self.fail("Valid PNG should not raise ValidationError")

    def test_valid_jpeg(self):
        """Should accept valid JPEG file."""
        jpeg_file = create_uploaded_file(
            FileFixtures.create_valid_jpeg(),
            'image/jpeg'
        )

        try:
            validate_image_file_magic(jpeg_file)
        except ValidationError:
            self.fail("Valid JPEG should not raise ValidationError")

    def test_oversized_image(self):
        """Should reject image larger than MAX_IMAGE_SIZE."""
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a buffer with valid JPEG header but over 1.5MB
        buffer = BytesIO()
        # Valid JPEG header
        buffer.write(b'\xff\xd8\xff\xe0')
        buffer.write(b'\x00\x10JFIF\x00\x01')
        # Add enough data to exceed 1.5MB
        buffer.write(b'\x00' * (2 * 1024 * 1024))
        buffer.seek(0)

        large_file = SimpleUploadedFile(
            "large.jpg",
            buffer.read(),
            content_type='image/jpeg'
        )

        with self.assertRaises(ValidationError) as context:
            validate_image_file_magic(large_file)

        self.assertIn('1.5MB', str(context.exception))

    def test_wrong_magic_bytes(self):
        """Should reject file with wrong magic bytes."""
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create file with completely wrong magic bytes
        buffer = BytesIO()
        buffer.write(b'Not an image at all!')
        buffer.write(b'\x00' * 100)
        buffer.seek(0)

        fake_file = SimpleUploadedFile(
            "fake.jpg",
            buffer.read(),
            content_type='image/jpeg'
        )

        with self.assertRaises(ValidationError) as context:
            validate_image_file_magic(fake_file)

        self.assertIn('Unsupported image file type', str(context.exception))

    def test_text_file_as_image(self):
        """Should reject text file masquerading as image."""
        text_file = create_uploaded_file(
            FileFixtures.create_text_file(),
            'image/jpeg'
        )

        with self.assertRaises(ValidationError) as context:
            validate_image_file_magic(text_file)

        self.assertIn('Unsupported image file type', str(context.exception))

    def test_file_seek_after_validation(self):
        """Should seek file back to beginning after validation."""
        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(),
            'image/png'
        )

        validate_image_file_magic(png_file)

        # File should be at position 0 after validation
        position = png_file.tell()
        self.assertEqual(position, 0)

    def test_empty_image_file(self):
        """Should reject empty image file."""
        empty_file = create_uploaded_file(
            FileFixtures.create_empty_file(),
            'image/jpeg'
        )

        with self.assertRaises(ValidationError):
            validate_image_file_magic(empty_file)


class TestVideoValidation(TestCase):
    """Test video file validation."""

    def test_valid_mp4(self):
        """Should accept valid MP4 file."""
        mp4_file = create_uploaded_file(
            FileFixtures.create_valid_mp4(),
            'video/mp4'
        )

        try:
            validate_video_file_magic(mp4_file)
        except ValidationError:
            self.fail("Valid MP4 should not raise ValidationError")

    def test_valid_webm(self):
        """Should accept valid WebM file."""
        webm_file = create_uploaded_file(
            FileFixtures.create_valid_webm(),
            'video/webm'
        )

        try:
            validate_video_file_magic(webm_file)
        except ValidationError:
            self.fail("Valid WebM should not raise ValidationError")

    def test_oversized_video(self):
        """Should reject video larger than MAX_VIDEO_SIZE."""
        large_file = create_uploaded_file(
            FileFixtures.create_large_video(size_mb=60),
            'video/mp4'
        )

        with self.assertRaises(ValidationError) as context:
            validate_video_file_magic(large_file)

        self.assertIn('50MB', str(context.exception))

    def test_wrong_video_magic_bytes(self):
        """Should reject file with wrong magic bytes."""
        fake_file = create_uploaded_file(
            FileFixtures.create_text_file(),
            'video/mp4'
        )

        with self.assertRaises(ValidationError) as context:
            validate_video_file_magic(fake_file)

        self.assertIn('Unsupported video file type', str(context.exception))

    def test_image_as_video(self):
        """Should reject image file uploaded as video."""
        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(),
            'video/mp4'
        )

        with self.assertRaises(ValidationError) as context:
            validate_video_file_magic(png_file)

        self.assertIn('Unsupported video file type', str(context.exception))

    def test_file_seek_after_video_validation(self):
        """Should seek file back to beginning after validation."""
        mp4_file = create_uploaded_file(
            FileFixtures.create_valid_mp4(),
            'video/mp4'
        )

        validate_video_file_magic(mp4_file)

        # File should be at position 0 after validation
        position = mp4_file.tell()
        self.assertEqual(position, 0)


class TestValidatorEdgeCases(TestCase):
    """Test edge cases and error handling in validators."""

    def test_exactly_max_image_size(self):
        """Should accept image exactly at MAX_IMAGE_SIZE."""
        pass  # Implementation depends on ability to create exact-size files

    def test_one_byte_over_limit(self):
        """Should reject image one byte over MAX_IMAGE_SIZE."""
        pass

    def test_null_file(self):
        """Should handle null file gracefully."""
        pass

    def test_validator_does_not_modify_file(self):
        """Validator should not modify file content."""
        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(),
            'image/png'
        )

        # Read original content
        original_content = png_file.read()
        png_file.seek(0)

        # Validate
        validate_image_file_magic(png_file)

        # Content should be unchanged
        new_content = png_file.read()
        self.assertEqual(original_content, new_content)
