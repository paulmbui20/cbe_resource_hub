"""
Test fixtures and helpers for file upload tests.
Generates valid and invalid test files with proper magic bytes.
"""
from io import BytesIO
from PIL import Image
import struct


class FileFixtures:
    """Factory for generating test files with correct magic bytes."""

    @staticmethod
    def create_valid_png(width=100, height=100):
        """Create a valid PNG image."""
        img = Image.new('RGB', (width, height), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        buffer.name = 'test.png'
        return buffer

    @staticmethod
    def create_valid_jpeg(width=100, height=100):
        """Create a valid JPEG image."""
        img = Image.new('RGB', (width, height), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        buffer.name = 'test.jpg'
        return buffer

    @staticmethod
    def create_large_image(size_mb=2):
        """Create an image larger than allowed size (for testing size validation)."""
        # Create a large image (approximately size_mb MB)
        dimension = int((size_mb * 1024 * 1024 / 3) ** 0.5)
        img = Image.new('RGB', (dimension, dimension), color='green')
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=100)
        buffer.seek(0)
        buffer.name = 'large.jpg'
        return buffer

    @staticmethod
    def create_fake_image_with_wrong_magic():
        """Create a file with .jpg extension but wrong magic bytes."""
        buffer = BytesIO()
        # Write PNG magic bytes but name it as JPEG
        buffer.write(b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a')
        buffer.write(b'\x00' * 100)  # Padding
        buffer.seek(0)
        buffer.name = 'fake.jpg'
        return buffer

    @staticmethod
    def create_text_file():
        """Create a plain text file (should be rejected for image validation)."""
        buffer = BytesIO()
        buffer.write(b'This is a text file, not an image!')
        buffer.seek(0)
        buffer.name = 'text.txt'
        return buffer

    @staticmethod
    def create_valid_mp4():
        """Create a minimal valid MP4 file."""
        buffer = BytesIO()
        # MP4 file header (ftyp box)
        # Box size (4 bytes) + box type (4 bytes) + major brand (4 bytes) + minor version (4 bytes)
        ftyp_box = struct.pack('>I', 32)  # Box size
        ftyp_box += b'ftyp'  # Box type
        ftyp_box += b'mp42'  # Major brand
        ftyp_box += struct.pack('>I', 0)  # Minor version
        ftyp_box += b'mp42' + b'isom'  # Compatible brands

        buffer.write(ftyp_box)
        # Add some padding to make it larger
        buffer.write(b'\x00' * 1000)
        buffer.seek(0)
        buffer.name = 'test.mp4'
        return buffer

    @staticmethod
    def create_valid_webm():
        """Create a minimal valid WebM file."""
        buffer = BytesIO()
        # WebM/EBML header
        buffer.write(b'\x1a\x45\xdf\xa3')  # EBML header
        buffer.write(b'\x00' * 1000)  # Padding
        buffer.seek(0)
        buffer.name = 'test.webm'
        return buffer

    @staticmethod
    def create_large_video(size_mb=60):
        """Create a video larger than allowed size."""
        buffer = BytesIO()
        # MP4 header
        ftyp_box = struct.pack('>I', 32)
        ftyp_box += b'ftyp'
        ftyp_box += b'mp42'
        ftyp_box += struct.pack('>I', 0)
        ftyp_box += b'mp42' + b'isom'

        buffer.write(ftyp_box)
        # Fill with zeros to reach desired size
        buffer.write(b'\x00' * (size_mb * 1024 * 1024))
        buffer.seek(0)
        buffer.name = 'large.mp4'
        return buffer

    @staticmethod
    def create_pdf():
        """Create a minimal PDF file."""
        buffer = BytesIO()
        buffer.write(b'%PDF-1.4\n')
        buffer.write(b'1 0 obj\n<< /Type /Catalog >>\nendobj\n')
        buffer.write(b'%%EOF\n')
        buffer.seek(0)
        buffer.name = 'test.pdf'
        return buffer

    @staticmethod
    def create_zip():
        """Create a minimal ZIP file."""
        buffer = BytesIO()
        # ZIP file signature
        buffer.write(b'PK\x03\x04')
        buffer.write(b'\x00' * 100)
        buffer.seek(0)
        buffer.name = 'test.zip'
        return buffer

    @staticmethod
    def create_empty_file():
        """Create an empty file."""
        buffer = BytesIO()
        buffer.name = 'empty.dat'
        return buffer


class MockStorage:
    """Mock storage backend for testing without actual file I/O."""

    def __init__(self):
        self.files = {}
        self.deleted = []

    def save(self, name, content):
        """Mock save operation."""
        self.files[name] = content.read()
        return name

    def delete(self, name):
        """Mock delete operation."""
        if name in self.files:
            del self.files[name]
            self.deleted.append(name)

    def exists(self, name):
        """Mock exists check."""
        return name in self.files

    def url(self, name):
        """Mock URL generation."""
        return f'https://mock-r2.example.com/{name}'

    def size(self, name):
        """Mock size check."""
        if name in self.files:
            return len(self.files[name])
        return 0


def create_uploaded_file(buffer, content_type='application/octet-stream'):
    """
    Create a Django UploadedFile from BytesIO buffer.

    Args:
        buffer: BytesIO object with file content
        content_type: MIME type of the file

    Returns:
        SimpleUploadedFile instance
    """
    from django.core.files.uploadedfile import SimpleUploadedFile

    content = buffer.read()
    buffer.seek(0)

    return SimpleUploadedFile(
        name=buffer.name,
        content=content,
        content_type=content_type
    )
