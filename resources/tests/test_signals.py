"""
resources/tests/test_signals.py

Tests for resources/signals.py:
  - LearningArea post_save / post_delete clears list and per-object cache
  - Grade post_save / post_delete clears list and per-object cache
  - EducationLevel post_save / post_delete clears list and per-object cache
"""

from django.core.cache import cache
from django.test import TestCase

from resources.models import EducationLevel, Grade, LearningArea
from resources.tests.base import ResourceBaseTestCase


class LearningAreaSignalTests(ResourceBaseTestCase):

    LIST_KEY = "resources:learning_areas"

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _obj_key(self, slug):
        return f"resources:learningarea:{slug}"

    def test_post_save_clears_list_cache(self):
        cache.set(self.LIST_KEY, ["stale"], 60)
        la = LearningArea.objects.create(name="Unique Subject")
        self.assertIsNone(cache.get(self.LIST_KEY))

    def test_post_delete_clears_list_cache(self):
        la = LearningArea.objects.create(name="Delete Me Subject")
        cache.set(self.LIST_KEY, ["stale"], 60)
        la.delete()
        self.assertIsNone(cache.get(self.LIST_KEY))

    def test_post_save_clears_per_object_cache(self):
        la = LearningArea.objects.create(name="Cached Subject")
        key = self._obj_key(la.slug)
        cache.set(key, la, 60)
        la.save()
        self.assertIsNone(cache.get(key))

    def test_post_delete_clears_per_object_cache(self):
        la = LearningArea.objects.create(name="Delete Cache Subject")
        key = self._obj_key(la.slug)
        cache.set(key, la, 60)
        la.delete()
        self.assertIsNone(cache.get(key))


class GradeSignalTests(ResourceBaseTestCase):

    LIST_KEY = "resources:grades"

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _obj_key(self, slug):
        return f"resources:grade:{slug}"

    def test_post_save_clears_list_cache(self):
        cache.set(self.LIST_KEY, ["stale"], 60)
        Grade.objects.create(level=self.level, name="Grade X", order=99)
        self.assertIsNone(cache.get(self.LIST_KEY))

    def test_post_delete_clears_list_cache(self):
        g = Grade.objects.create(level=self.level, name="Grade Y", order=98)
        cache.set(self.LIST_KEY, ["stale"], 60)
        # Remove the resource that protects this grade first
        from resources.models import ResourceItem
        ResourceItem.objects.filter(grade=g).delete()
        g.delete()
        self.assertIsNone(cache.get(self.LIST_KEY))

    def test_post_save_clears_per_object_cache(self):
        g = Grade.objects.create(level=self.level, name="Grade Z", order=97)
        key = self._obj_key(g.slug)
        cache.set(key, g, 60)
        g.save()
        self.assertIsNone(cache.get(key))


class EducationLevelSignalTests(ResourceBaseTestCase):

    LIST_KEY = "resources:education_levels"

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _obj_key(self, slug):
        return f"resources:educationlevel:{slug}"

    def test_post_save_clears_list_cache(self):
        cache.set(self.LIST_KEY, ["stale"], 60)
        EducationLevel.objects.create(name="Senior Secondary", order=5)
        self.assertIsNone(cache.get(self.LIST_KEY))

    def test_post_delete_clears_list_cache(self):
        lvl = EducationLevel.objects.create(name="Junior Secondary", order=4)
        cache.set(self.LIST_KEY, ["stale"], 60)
        lvl.delete()
        self.assertIsNone(cache.get(self.LIST_KEY))

    def test_post_save_clears_per_object_cache(self):
        lvl = EducationLevel.objects.create(name="Pre-Primary", order=0)
        key = self._obj_key(lvl.slug)
        cache.set(key, lvl, 60)
        lvl.save()
        self.assertIsNone(cache.get(key))
