"""
core/tests/test_utils.py

Tests for core/utils.py:
  - current_year is the real calendar year
  - clear_object_cache deletes an existing cache entry
  - clear_object_cache is a no-op when the key is missing
"""

from datetime import datetime

from django.core.cache import cache
from django.test import TestCase

from core.models import AcademicSession
from core.utils import clear_object_cache, current_year


class CurrentYearTests(TestCase):

    def test_current_year_matches_calendar_year(self):
        self.assertEqual(current_year, datetime.now().year)

    def test_current_year_is_int(self):
        self.assertIsInstance(current_year, int)

    def test_current_year_is_reasonable(self):
        self.assertGreaterEqual(current_year, 2024)
        self.assertLessEqual(current_year, 2100)


class ClearObjectCacheTests(TestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _cache_key(self, model, slug):
        return f"{model._meta.app_label}:{model._meta.model_name}:{slug}"

    def test_clears_existing_cache_entry(self):
        key = self._cache_key(AcademicSession, "test-slug")
        cache.set(key, {"data": "cached"}, 60)
        self.assertIsNotNone(cache.get(key))

        clear_object_cache(AcademicSession, "test-slug")

        self.assertIsNone(cache.get(key))

    def test_noop_when_key_missing(self):
        # Should not raise even if the key was never set
        try:
            clear_object_cache(AcademicSession, "nonexistent-slug")
        except Exception as exc:
            self.fail(f"clear_object_cache raised unexpectedly: {exc}")

    def test_does_not_clear_other_keys(self):
        key_a = self._cache_key(AcademicSession, "slug-a")
        key_b = self._cache_key(AcademicSession, "slug-b")
        cache.set(key_a, "value-a", 60)
        cache.set(key_b, "value-b", 60)

        clear_object_cache(AcademicSession, "slug-a")

        self.assertIsNone(cache.get(key_a))
        self.assertEqual(cache.get(key_b), "value-b")
