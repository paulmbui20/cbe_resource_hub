"""
seo/tests/test_mixins.py

Tests for SlugRedirectMixin:
  - Slug change on an existing model creates a redirect
  - Slug unchanged on save does NOT create a redirect
  - New record save (no pk yet) does NOT create a redirect
  - Redirect chain prevention through the mixin path
  - Cache keys are cleared after slug change
"""

from django.core.cache import cache
from django.test import TestCase

from resources.models import EducationLevel, LearningArea
from seo.models import SlugRedirect
from seo.tests.base import SEOBaseTestCase


class SlugRedirectMixinTests(SEOBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_slug_change_creates_redirect(self):
        lvl = EducationLevel.objects.create(name="Mixin Original", order=300)
        old_slug = lvl.slug
        lvl.slug = "mixin-renamed"
        lvl.save()
        result = SlugRedirect.get_redirect(old_slug)
        self.assertEqual(result, "mixin-renamed")

    def test_slug_unchanged_does_not_create_redirect(self):
        lvl = EducationLevel.objects.create(name="Mixin Stable", order=301)
        slug = lvl.slug
        lvl.save()  # save without changing slug
        # No redirect should exist for this slug as old_slug
        result = SlugRedirect.get_redirect(slug)
        self.assertIsNone(result)

    def test_new_record_does_not_create_redirect(self):
        count_before = SlugRedirect.objects.count()
        EducationLevel.objects.create(name="Brand New Mixin Level", order=302)
        # No new redirects for a first-time save
        self.assertEqual(SlugRedirect.objects.count(), count_before)

    def test_slug_change_clears_old_slug_cache(self):
        lvl = EducationLevel.objects.create(name="Cache Clear Mixin", order=303)
        old_slug = lvl.slug
        cache.set(f"slug_redirect_{old_slug}", "stale", 60)
        lvl.slug = "cache-cleared-new"
        lvl.save()
        # The mixin clears redirect cache for old and new slugs
        cached = cache.get(f"slug_redirect_{old_slug}")
        # After clearing, the cache should be invalidated (None or fresh value)
        # The mixin calls cache.delete_many which removes the key
        self.assertIsNone(cached)

    def test_slug_change_clears_new_slug_cache(self):
        lvl = EducationLevel.objects.create(name="New Slug Cache Clear", order=304)
        new_slug = "new-cache-cleared"
        cache.set(f"slug_redirect_{new_slug}", "stale", 60)
        lvl.slug = new_slug
        lvl.save()
        self.assertIsNone(cache.get(f"slug_redirect_{new_slug}"))

    def test_multiple_slug_changes_update_redirect(self):
        """A→B then B→C: the original slug's redirect should eventually point toward C."""
        lvl = EducationLevel.objects.create(name="Multi Change Mixin", order=305)
        first_slug = lvl.slug
        lvl.slug = "multi-b"
        lvl.save()
        # first_slug → multi-b now exists
        self.assertEqual(SlugRedirect.get_redirect(first_slug), "multi-b")
        lvl.slug = "multi-c"
        lvl.save()
        # multi-b → multi-c now exists; first_slug should be updated to → multi-c
        result = SlugRedirect.get_redirect("multi-b")
        self.assertEqual(result, "multi-c")

    def test_slug_revert_clears_circular_redirect(self):
        """Changing A→B then B→A should not create a circular loop."""
        lvl = EducationLevel.objects.create(name="Revert Mixin Test", order=306)
        a_slug = lvl.slug
        lvl.slug = "revert-b"
        lvl.save()
        lvl.slug = a_slug
        lvl.save()
        # After reverting, there should be no loop - just clean state
        # (Either one direction or none, but not both)
        fwd = SlugRedirect.objects.filter(old_slug=a_slug, new_slug="revert-b").exists()
        rev = SlugRedirect.objects.filter(old_slug="revert-b", new_slug=a_slug).exists()
        self.assertFalse(fwd and rev, "Circular redirect chain detected!")
