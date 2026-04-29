"""
resources/tests/test_cache.py

Tests for resources/cache.py:
  - Each getter returns data and populates cache on first call
  - Subsequent calls hit cache (no new DB queries)
  - Empty DB result is NOT cached
  - get_slug_based_object_or_404_with_cache returns object, raises 404 for missing
  - get_resource_types returns a dict
"""

from django.core.cache import cache
from django.test import TestCase

from resources.cache import (
    get_academic_sessions,
    get_education_levels,
    get_grades,
    get_learning_areas,
    get_resource_types,
    get_slug_based_object_or_404_with_cache,
)
from resources.models import EducationLevel, Grade, LearningArea
from resources.tests.base import ResourceBaseTestCase


class GetLearningAreasTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_queryset_with_data(self):
        areas = get_learning_areas()
        self.assertIn(self.learning_area, list(areas))

    def test_populates_cache(self):
        get_learning_areas()
        self.assertIsNotNone(cache.get("resources:learning_areas"))

    def test_second_call_uses_cache(self):
        get_learning_areas()
        with self.assertNumQueries(0):
            get_learning_areas()

    def test_empty_db_not_cached(self):
        """If the DB has no learning areas the cache key should NOT be set."""
        # Use a clean test DB state by checking that an empty queryset avoids caching.
        # We verify this indirectly: clear the cache, patch the queryset to return
        # an empty result, and confirm the key is still None afterwards.
        from unittest.mock import patch
        cache.delete("resources:learning_areas")
        empty_qs = LearningArea.objects.none()
        # Make objects.all() return an empty queryset so the exists() check fails
        with patch("resources.cache.LearningArea.objects") as mock_mgr:
            mock_mgr.all.return_value.prefetch_related.return_value = empty_qs
            get_learning_areas()
        self.assertIsNone(cache.get("resources:learning_areas"))


class GetGradesTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_queryset_with_data(self):
        grades = get_grades()
        self.assertIn(self.grade, list(grades))

    def test_populates_cache(self):
        get_grades()
        self.assertIsNotNone(cache.get("resources:grades"))

    def test_second_call_uses_cache(self):
        get_grades()
        with self.assertNumQueries(0):
            get_grades()


class GetEducationLevelsTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_queryset_with_data(self):
        levels = get_education_levels()
        self.assertIn(self.level, list(levels))

    def test_populates_cache(self):
        get_education_levels()
        self.assertIsNotNone(cache.get("resources:education_levels"))

    def test_second_call_uses_cache(self):
        get_education_levels()
        with self.assertNumQueries(0):
            get_education_levels()


class GetResourceTypesTests(TestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_dict(self):
        types = get_resource_types()
        self.assertIsInstance(types, dict)

    def test_dict_has_expected_keys(self):
        types = get_resource_types()
        self.assertIn("lesson_plan", types)
        self.assertIn("exam", types)
        self.assertIn("notes", types)

    def test_populates_cache(self):
        get_resource_types()
        self.assertIsNotNone(cache.get("resources:resource_types"))

    def test_second_call_uses_cache(self):
        get_resource_types()
        with self.assertNumQueries(0):
            get_resource_types()


class GetSlugBasedObjectTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_existing_object(self):
        obj = get_slug_based_object_or_404_with_cache(EducationLevel, self.level.slug)
        self.assertEqual(obj.pk, self.level.pk)

    def test_caches_result(self):
        get_slug_based_object_or_404_with_cache(EducationLevel, self.level.slug)
        key = f"resources:educationlevel:{self.level.slug}"
        self.assertIsNotNone(cache.get(key))

    def test_second_call_uses_cache(self):
        get_slug_based_object_or_404_with_cache(EducationLevel, self.level.slug)
        with self.assertNumQueries(0):
            get_slug_based_object_or_404_with_cache(EducationLevel, self.level.slug)

    def test_missing_slug_raises_404(self):
        from django.http import Http404
        with self.assertRaises(Http404):
            get_slug_based_object_or_404_with_cache(EducationLevel, "nonexistent-slug")

    def test_works_for_grade_model(self):
        obj = get_slug_based_object_or_404_with_cache(Grade, self.grade.slug)
        self.assertEqual(obj.pk, self.grade.pk)

    def test_works_for_learning_area_model(self):
        obj = get_slug_based_object_or_404_with_cache(LearningArea, self.learning_area.slug)
        self.assertEqual(obj.pk, self.learning_area.pk)


class GetAcademicSessionsTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_queryset_with_data(self):
        sessions = get_academic_sessions()
        self.assertIn(self.session, list(sessions))

    def test_populates_cache(self):
        get_academic_sessions()
        self.assertIsNotNone(cache.get("resources:academic_sessions"))

    def test_second_call_uses_cache(self):
        get_academic_sessions()
        with self.assertNumQueries(0):
            get_academic_sessions()
