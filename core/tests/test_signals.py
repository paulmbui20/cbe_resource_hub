"""
core/tests/test_signals.py

Tests for core/signals.py:
  - AcademicSession post_save clears "resources:academic_sessions" cache
  - AcademicSession post_delete clears "resources:academic_sessions" cache
  - AcademicSession post_save clears the per-object slug cache
  - Term post_save / post_delete clears list cache
  - Year post_save / post_delete clears list cache
"""

from django.core.cache import cache
from django.test import TestCase

from core.models import AcademicSession, Term, Year

_LIST_CACHE_KEY = "resources:academic_sessions"


class AcademicSessionSignalTests(TestCase):

    def setUp(self):
        cache.clear()
        self.year = Year.objects.create(year=2040)
        self.term = Term.objects.create(term_number=4)

    def tearDown(self):
        cache.clear()

    def _object_cache_key(self, slug):
        return f"core:academicsession:{slug}"

    def test_post_save_clears_list_cache(self):
        cache.set(_LIST_CACHE_KEY, ["stale data"], 60)
        s = AcademicSession.objects.create(
            current_year=self.year, current_term=self.term
        )
        self.assertIsNone(cache.get(_LIST_CACHE_KEY))

    def test_post_delete_clears_list_cache(self):
        s = AcademicSession.objects.create(
            current_year=self.year, current_term=self.term
        )
        cache.set(_LIST_CACHE_KEY, ["stale data"], 60)
        s.delete()
        self.assertIsNone(cache.get(_LIST_CACHE_KEY))

    def test_post_save_clears_per_object_cache(self):
        s = AcademicSession.objects.create(
            current_year=self.year, current_term=self.term
        )
        obj_key = self._object_cache_key(s.slug)
        cache.set(obj_key, {"cached": True}, 60)
        # trigger save signal
        s.save()
        self.assertIsNone(cache.get(obj_key))

    def test_post_delete_clears_per_object_cache(self):
        s = AcademicSession.objects.create(
            current_year=self.year, current_term=self.term
        )
        obj_key = self._object_cache_key(s.slug)
        cache.set(obj_key, {"cached": True}, 60)
        s.delete()
        self.assertIsNone(cache.get(obj_key))


class TermSignalTests(TestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_term_post_save_clears_list_cache(self):
        cache.set(_LIST_CACHE_KEY, ["stale"], 60)
        Term.objects.create(term_number=7)
        self.assertIsNone(cache.get(_LIST_CACHE_KEY))

    def test_term_post_delete_clears_list_cache(self):
        t = Term.objects.create(term_number=6)
        cache.set(_LIST_CACHE_KEY, ["stale"], 60)
        t.delete()
        self.assertIsNone(cache.get(_LIST_CACHE_KEY))


class YearSignalTests(TestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_year_post_save_clears_list_cache(self):
        cache.set(_LIST_CACHE_KEY, ["stale"], 60)
        Year.objects.create(year=2055)
        self.assertIsNone(cache.get(_LIST_CACHE_KEY))

    def test_year_post_delete_clears_list_cache(self):
        y = Year.objects.create(year=2056)
        cache.set(_LIST_CACHE_KEY, ["stale"], 60)
        y.delete()
        self.assertIsNone(cache.get(_LIST_CACHE_KEY))
