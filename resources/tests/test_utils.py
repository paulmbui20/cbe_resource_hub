"""
resources/tests/test_utils.py

Tests for resources/utils.py:
  - file_upload_path: generates path with grade, resource_type, year, month
  - file_upload_path: handles missing extension gracefully
  - PublicFilesStorageCallable: returns FileSystemStorage in test context
  - get_year_and_month_from_created_at_datetime: returns correct tuple
"""

from datetime import datetime
from unittest.mock import MagicMock

from django.core.files.storage import FileSystemStorage
from django.test import TestCase

from resources.utils import (
    PublicFilesStorageCallable,
    file_upload_path,
    get_year_and_month_from_created_at_datetime,
)


class GetYearAndMonthTests(TestCase):

    def test_returns_correct_year(self):
        dt = datetime(2025, 7, 15)
        year, month = get_year_and_month_from_created_at_datetime(dt)
        self.assertEqual(year, 2025)

    def test_returns_correct_month(self):
        dt = datetime(2025, 7, 15)
        year, month = get_year_and_month_from_created_at_datetime(dt)
        self.assertEqual(month, 7)

    def test_returns_tuple(self):
        dt = datetime(2024, 1, 1)
        result = get_year_and_month_from_created_at_datetime(dt)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


class FileUploadPathTests(TestCase):

    def _instance(self, title="My Resource", resource_type="notes", grade="grade-1"):
        instance = MagicMock()
        instance.title = title
        instance.resource_type = resource_type
        instance.grade = grade
        instance.created_at = datetime(2025, 4, 1)
        return instance

    def test_path_contains_grade(self):
        path = file_upload_path(self._instance(), "report.pdf")
        self.assertIn("grade-1", path)

    def test_path_contains_resource_type(self):
        path = file_upload_path(self._instance(), "report.pdf")
        self.assertIn("notes", path)

    def test_path_contains_year(self):
        path = file_upload_path(self._instance(), "report.pdf")
        self.assertIn("2025", path)

    def test_path_contains_month(self):
        path = file_upload_path(self._instance(), "report.pdf")
        self.assertIn("4", path)

    def test_path_contains_extension(self):
        path = file_upload_path(self._instance(), "report.pdf")
        self.assertTrue(path.endswith(".pdf"))

    def test_path_contains_uuid(self):
        import re
        path = file_upload_path(self._instance(), "report.pdf")
        # UUID pattern in filename
        self.assertRegex(path, r"[0-9a-f\-]{36}")

    def test_no_extension_handled(self):
        path = file_upload_path(self._instance(), "report_no_ext")
        self.assertIsNotNone(path)

    def test_empty_title_uses_fallback(self):
        instance = self._instance(title="")
        path = file_upload_path(instance, "file.pdf")
        # Should use 'resource item file' as fallback
        self.assertIn("resource", path.lower())

    def test_missing_resource_type_no_crash(self):
        instance = self._instance()
        instance.resource_type = None
        path = file_upload_path(instance, "file.pdf")
        self.assertIsNotNone(path)


class PublicFilesStorageCallableTests(TestCase):

    def test_returns_filesystem_storage_in_tests(self):
        """In test context pytest is in sys.modules → FileSystemStorage used."""
        storage = PublicFilesStorageCallable()()
        self.assertIsInstance(storage, FileSystemStorage)
