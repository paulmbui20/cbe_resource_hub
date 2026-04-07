"""
Unit tests for management commands - FIXED VERSION.
"""
from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from unittest.mock import patch

from files.models import File
from .fixtures import FileFixtures, create_uploaded_file


class TestCheckOrphanedFilesCommand(TestCase):
    """Test check_orphaned_files management command."""

    def setUp(self):
        """Create test files."""
        # Create valid file
        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(),
            'image/png'
        )
        self.valid_file = File.objects.create(
            title="Valid File",
            file=png_file
        )

    def test_command_runs_without_error(self):
        """Command should run without errors."""
        out = StringIO()

        # Mock input to avoid stdin issues
        with patch('builtins.input', return_value='no'):
            try:
                call_command('check_orphaned_files', stdout=out)
            except Exception as e:
                self.fail(f"Command should run without error: {e}")

    def test_command_finds_no_orphans_when_all_exist(self):
        """Should report no orphans when all files exist."""
        out = StringIO()

        with patch('builtins.input', return_value='no'):
            call_command('check_orphaned_files', stdout=out)

        output = out.getvalue()
        self.assertIn('No orphaned files', output)

    @patch.object(File, 'file_exists')
    def test_command_detects_orphaned_files(self, mock_exists):
        """Should detect orphaned files."""
        mock_exists.return_value = False

        out = StringIO()

        # Mock input to prevent stdin error
        with patch('builtins.input', return_value='no'):
            call_command('check_orphaned_files', stdout=out)

        output = out.getvalue()
        self.assertIn('Orphaned', output)
        self.assertIn(self.valid_file.title, output)

    @patch.object(File, 'file_exists')
    @patch('builtins.input')
    def test_command_deletes_orphans_on_confirmation(self, mock_input, mock_exists):
        """Should delete orphaned files when user confirms."""
        mock_exists.return_value = False
        mock_input.return_value = 'yes'

        initial_count = File.objects.count()

        out = StringIO()
        call_command('check_orphaned_files', stdout=out)

        # File should be deleted
        self.assertEqual(File.objects.count(), initial_count - 1)

    @patch.object(File, 'file_exists')
    @patch('builtins.input')
    def test_command_keeps_orphans_on_rejection(self, mock_input, mock_exists):
        """Should not delete orphaned files when user declines."""
        mock_exists.return_value = False
        mock_input.return_value = 'no'

        initial_count = File.objects.count()

        out = StringIO()
        call_command('check_orphaned_files', stdout=out)

        # File should not be deleted
        self.assertEqual(File.objects.count(), initial_count)


class TestRegenerateMetadataCommand(TestCase):
    """Test regenerate_metadata management command."""

    def setUp(self):
        """Create test files."""
        # Create files with metadata
        for i in range(3):
            png_file = create_uploaded_file(
                FileFixtures.create_valid_png(),
                'image/png'
            )
            File.objects.create(title=f"Test {i}", file=png_file)

        # Create video
        mp4_file = create_uploaded_file(
            FileFixtures.create_valid_mp4(),
            'video/mp4'
        )
        File.objects.create(title="Video", file=mp4_file)

    def test_command_runs_without_error(self):
        """Command should run without errors."""
        out = StringIO()

        try:
            call_command('regenerate_metadata', stdout=out)
        except Exception as e:
            self.fail(f"Command should run without error: {e}")

    def test_command_regenerates_all_files(self):
        """Should process all files."""
        # Corrupt metadata for all files
        File.objects.update(width=None, height=None)

        out = StringIO()
        call_command('regenerate_metadata', stdout=out)

        # All images should have dimensions restored
        images = File.objects.filter(file_category='image')
        for img in images:
            self.assertIsNotNone(img.width)
            self.assertIsNotNone(img.height)

    def test_command_filters_by_category(self):
        """Should only process files of specified category."""
        # Corrupt all metadata
        File.objects.update(width=None, height=None)

        out = StringIO()
        call_command('regenerate_metadata', category='image', stdout=out)

        # Only images should be processed
        images = File.objects.filter(file_category='image')
        videos = File.objects.filter(file_category='video')

        for img in images:
            self.assertIsNotNone(img.width)

        # Videos dimensions should still be None
        for vid in videos:
            self.assertIsNone(vid.width)

    def test_command_reports_success_count(self):
        """Should report number of successful regenerations."""
        out = StringIO()
        call_command('regenerate_metadata', stdout=out)

        output = out.getvalue()
        self.assertIn('Success', output)
        # Should mention number of files
        total = File.objects.count()
        self.assertIn(str(total), output)

    def test_command_handles_errors_gracefully(self):
        """Should continue processing if some files fail."""
        with patch.object(File, '_extract_metadata') as mock_extract:
            # Make first call fail, rest succeed
            mock_extract.side_effect = [Exception("Error"), None, None, None]

            out = StringIO()
            call_command('regenerate_metadata', stdout=out)

            output = out.getvalue()
            # Should report both success and failure
            self.assertIn('Failed', output)


class TestCalculateFileHashesCommand(TestCase):
    """Test calculate_file_hashes management command."""

    def setUp(self):
        """Create test files without hashes."""
        for i in range(3):
            png_file = create_uploaded_file(
                FileFixtures.create_valid_png(width=10 + i, height=10 + i),
                'image/png'
            )
            File.objects.create(title=f"Test {i}", file=png_file)

    def test_command_runs_without_error(self):
        """Command should run without errors."""
        out = StringIO()

        try:
            call_command('calculate_file_hashes', stdout=out)
        except Exception as e:
            self.fail(f"Command should run without error: {e}")

    def test_command_calculates_missing_hashes(self):
        """Should calculate hashes for files without them."""
        # Ensure files have no hashes
        File.objects.update(file_hash='')

        out = StringIO()
        call_command('calculate_file_hashes', stdout=out)

        # All files should now have hashes
        files = File.objects.all()
        for f in files:
            self.assertNotEqual(f.file_hash, '')
            self.assertEqual(len(f.file_hash), 64)  # SHA256 length

    def test_command_skips_files_with_hashes(self):
        """Should skip files that already have hashes."""
        # Give one file a hash
        file_with_hash = File.objects.first()
        file_with_hash.file_hash = 'a' * 64
        file_with_hash.save()

        out = StringIO()
        call_command('calculate_file_hashes', stdout=out)

        # Command should complete successfully
        output = out.getvalue()
        self.assertIn('Completed', output)

    def test_command_reports_completion(self):
        """Should report completion statistics."""
        File.objects.update(file_hash='')

        out = StringIO()
        call_command('calculate_file_hashes', stdout=out)

        output = out.getvalue()
        self.assertIn('Completed', output)
        self.assertIn('Success', output)


class TestManagementCommandsEdgeCases(TestCase):
    """Test edge cases in management commands."""

    def test_commands_with_no_files(self):
        """Commands should handle empty database gracefully."""
        # Ensure no files exist
        File.objects.all().delete()

        out = StringIO()

        # All commands should run without error
        try:
            with patch('builtins.input', return_value='no'):
                call_command('check_orphaned_files', stdout=out)
            call_command('regenerate_metadata', stdout=out)
            call_command('calculate_file_hashes', stdout=out)
        except Exception as e:
            self.fail(f"Commands should handle empty DB: {e}")

    def test_command_output_format(self):
        """Commands should produce readable output."""
        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(),
            'image/png'
        )
        File.objects.create(title="Test", file=png_file)

        out = StringIO()
        call_command('regenerate_metadata', stdout=out)

        output = out.getvalue()
        # Should have some output
        self.assertGreater(len(output), 0)
        # Should be readable (no raw exceptions or stack traces in normal operation)
        self.assertNotIn('Traceback', output)


class TestCommandsWithBrokenFiles(TestCase):
    """Test commands behavior with broken/corrupted files."""

    def test_regenerate_with_corrupted_files(self):
        """Should handle corrupted files gracefully."""
        # Create a file with corrupted data
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        buffer = BytesIO()
        buffer.write(b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a')  # PNG header
        buffer.write(b'\x00' * 100)  # Invalid data

        corrupted_file = SimpleUploadedFile(
            "corrupted.png",
            buffer.getvalue(),
            "image/png"
        )

        File.objects.create(title="Corrupted", file=corrupted_file)

        out = StringIO()

        # Should not crash
        try:
            call_command('regenerate_metadata', stdout=out)
        except Exception as e:
            self.fail(f"Should handle corrupted files: {e}")

    @patch.object(File, '_calculate_file_hash')
    def test_hash_calculation_with_errors(self, mock_hash):
        """Should handle hash calculation errors."""
        mock_hash.side_effect = Exception("Hash error")

        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(),
            'image/png'
        )
        File.objects.create(title="Test", file=png_file)

        out = StringIO()

        # Should continue despite errors
        call_command('calculate_file_hashes', stdout=out)

        output = out.getvalue()
        # Should report failure
        self.assertIn('Failed', output)
