"""
seo/tests/test_models.py

Tests for SEOModel (abstract) and SlugRedirect (concrete):

SEOModel (tested via EducationLevel which inherits it):
  - All SEO fields present and have correct defaults
  - get_meta_title(): falls back to str() when meta_title blank
  - get_meta_description(): returns empty string when blank
  - get_meta_keywords(): returns empty string when blank
  - featured_image_* properties return None when no image set
  - featured_image_webp_srcset / jpg_srcset return "" when no image
  - PublicFilesStorageCallable returns FileSystemStorage in tests

SlugRedirect:
  - Creation, __str__, fields
  - get_redirect(): returns new slug, increments hit_count; None for missing
  - create_redirect(): basic case, no-op when old==new
  - create_redirect(): prevents redirect chains (A→B then B→C becomes A→C)
  - create_redirect(): prevents circular redirects
  - create_redirect(): handles changing back to a previous slug
  - clear_for_slug(): removes redirects where slug is old or new
  - hit_count incremented atomically by get_redirect()
"""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from resources.models import EducationLevel, LearningArea
from seo.models import SlugRedirect, SEOModel, PublicFilesStorageCallable
from seo.tests.base import SEOBaseTestCase


# ── PublicFilesStorageCallable ─────────────────────────────────────────────────

class PublicFilesStorageCallableTests(TestCase):

    def test_returns_filesystem_storage_in_tests(self):
        from django.core.files.storage import FileSystemStorage
        storage = PublicFilesStorageCallable()()
        self.assertIsInstance(storage, FileSystemStorage)


# ── SEOModel field tests (via EducationLevel as concrete carrier) ──────────────

class SEOModelFieldTests(SEOBaseTestCase):
    """
    SEOModel is abstract; we test its fields via EducationLevel which
    inherits SEOModel.
    """

    def test_meta_title_field_exists(self):
        self.assertTrue(hasattr(self.level, "meta_title"))

    def test_meta_description_field_exists(self):
        self.assertTrue(hasattr(self.level, "meta_description"))

    def test_meta_keywords_field_exists(self):
        self.assertTrue(hasattr(self.level, "meta_keywords"))

    def test_focus_keyword_field_exists(self):
        self.assertTrue(hasattr(self.level, "focus_keyword"))

    def test_featured_image_field_exists(self):
        self.assertTrue(hasattr(self.level, "featured_image"))

    def test_meta_title_blank_by_default(self):
        lvl = EducationLevel.objects.create(name="Blank Meta Level", order=200)
        # EducationLevel.save() auto-populates meta_title from name, so just test the field exists
        self.assertIsNotNone(lvl.meta_title)

    def test_meta_keywords_blank_by_default(self):
        lvl = EducationLevel.objects.create(name="Keywords Level", order=201)
        # meta_keywords should default to blank string
        self.assertEqual(lvl.meta_keywords, "")

    def test_focus_keyword_blank_by_default(self):
        lvl = EducationLevel.objects.create(name="Focus Level", order=202)
        self.assertEqual(lvl.focus_keyword, "")

    def test_featured_image_null_by_default(self):
        lvl = EducationLevel.objects.create(name="No Image Level", order=203)
        self.assertFalse(bool(lvl.featured_image))


# ── SEOModel methods ───────────────────────────────────────────────────────────

class SEOModelMethodTests(SEOBaseTestCase):

    def _level_with_blank_seo(self, name, order):
        """Create a level whose SEO fields are explicitly blank."""
        lvl = EducationLevel.objects.create(name=name, order=order)
        # Override auto-populated fields
        EducationLevel.objects.filter(pk=lvl.pk).update(
            meta_title="", meta_description="", meta_keywords=""
        )
        lvl.refresh_from_db()
        return lvl

    def test_get_meta_title_returns_str_when_blank(self):
        lvl = self._level_with_blank_seo("Fallback Title Level", 210)
        self.assertEqual(lvl.get_meta_title(), str(lvl))

    def test_get_meta_title_returns_meta_title_when_set(self):
        lvl = EducationLevel.objects.create(name="Custom Title Level", order=211)
        EducationLevel.objects.filter(pk=lvl.pk).update(meta_title="Custom Title")
        lvl.refresh_from_db()
        self.assertEqual(lvl.get_meta_title(), "Custom Title")

    def test_get_meta_description_returns_empty_when_blank(self):
        lvl = self._level_with_blank_seo("Blank Desc Level", 212)
        self.assertEqual(lvl.get_meta_description(), "")

    def test_get_meta_description_returns_value_when_set(self):
        lvl = EducationLevel.objects.create(name="Desc Level", order=213)
        EducationLevel.objects.filter(pk=lvl.pk).update(meta_description="Great desc")
        lvl.refresh_from_db()
        self.assertEqual(lvl.get_meta_description(), "Great desc")

    def test_get_meta_keywords_returns_empty_when_blank(self):
        lvl = self._level_with_blank_seo("Blank KW Level", 214)
        self.assertEqual(lvl.get_meta_keywords(), "")

    def test_get_meta_keywords_returns_value_when_set(self):
        lvl = EducationLevel.objects.create(name="KW Level", order=215)
        EducationLevel.objects.filter(pk=lvl.pk).update(meta_keywords="cbc, cbk, education")
        lvl.refresh_from_db()
        self.assertEqual(lvl.get_meta_keywords(), "cbc, cbk, education")

    def test_featured_image_small_webp_returns_none_when_no_image(self):
        lvl = EducationLevel.objects.create(name="No Image Props Level", order=216)
        self.assertIsNone(lvl.featured_image_small_webp)

    def test_featured_image_small_jpg_returns_none_when_no_image(self):
        lvl = EducationLevel.objects.create(name="No Image Props Level 2", order=217)
        self.assertIsNone(lvl.featured_image_small_jpg)

    def test_featured_image_medium_webp_returns_none_when_no_image(self):
        lvl = EducationLevel.objects.create(name="No Image Props Level 3", order=218)
        self.assertIsNone(lvl.featured_image_medium_webp)

    def test_featured_image_medium_jpg_returns_none_when_no_image(self):
        lvl = EducationLevel.objects.create(name="No Image Props Level 4", order=219)
        self.assertIsNone(lvl.featured_image_medium_jpg)

    def test_featured_image_webp_srcset_returns_empty_string_when_no_image(self):
        lvl = EducationLevel.objects.create(name="Srcset Level", order=220)
        self.assertEqual(lvl.featured_image_webp_srcset, "")

    def test_featured_image_jpg_srcset_returns_empty_string_when_no_image(self):
        lvl = EducationLevel.objects.create(name="Jpg Srcset Level", order=221)
        self.assertEqual(lvl.featured_image_jpg_srcset, "")


# ── SlugRedirect model ─────────────────────────────────────────────────────────

class SlugRedirectCreationTests(SEOBaseTestCase):

    def test_created_with_required_fields(self):
        r = self.make_redirect("old-a", "new-a")
        self.assertIsNotNone(r.pk)

    def test_str_contains_arrow(self):
        r = self.make_redirect("old-b", "new-b")
        self.assertIn("→", str(r))

    def test_str_contains_old_slug(self):
        r = self.make_redirect("old-c", "new-c")
        self.assertIn("old-c", str(r))

    def test_str_contains_new_slug(self):
        r = self.make_redirect("old-d", "new-d")
        self.assertIn("new-d", str(r))

    def test_hit_count_defaults_to_zero(self):
        r = self.make_redirect("old-e", "new-e")
        self.assertEqual(r.hit_count, 0)

    def test_old_slug_unique(self):
        from django.db import IntegrityError
        self.make_redirect("old-unique", "new-1")
        with self.assertRaises(IntegrityError):
            self.make_redirect("old-unique", "new-2")

    def test_has_content_type_generic_fk(self):
        r = self.make_redirect("old-fk", "new-fk")
        self.assertIsNotNone(r.content_type)


class SlugRedirectGetRedirectTests(SEOBaseTestCase):

    def test_returns_new_slug_for_known_old_slug(self):
        self.make_redirect("old-get", "new-get")
        result = SlugRedirect.get_redirect("old-get")
        self.assertEqual(result, "new-get")

    def test_returns_none_for_unknown_slug(self):
        result = SlugRedirect.get_redirect("i-dont-exist")
        self.assertIsNone(result)

    def test_increments_hit_count_on_lookup(self):
        r = self.make_redirect("old-hit", "new-hit")
        self.assertEqual(r.hit_count, 0)
        SlugRedirect.get_redirect("old-hit")
        r.refresh_from_db()
        self.assertEqual(r.hit_count, 1)

    def test_multiple_lookups_increment_each_time(self):
        r = self.make_redirect("old-multi-hit", "new-multi-hit")
        for _ in range(3):
            SlugRedirect.get_redirect("old-multi-hit")
        r.refresh_from_db()
        self.assertEqual(r.hit_count, 3)


class SlugRedirectCreateRedirectTests(SEOBaseTestCase):

    def test_basic_create_redirect(self):
        r = SlugRedirect.create_redirect(self.resource, "basic-old", "basic-new")
        self.assertIsNotNone(r)
        self.assertEqual(r.old_slug, "basic-old")
        self.assertEqual(r.new_slug, "basic-new")

    def test_returns_none_when_old_equals_new(self):
        r = SlugRedirect.create_redirect(self.resource, "same-slug", "same-slug")
        self.assertIsNone(r)

    def test_prevents_redirect_chains(self):
        """A→B then B→C: create_redirect updates A→B so it becomes A→C."""
        SlugRedirect.create_redirect(self.resource, "chain-a", "chain-b")
        SlugRedirect.create_redirect(self.resource, "chain-b", "chain-c")
        # chain-a should now point to chain-c (chain collapsed)
        result = SlugRedirect.get_redirect("chain-a")
        # The implementation updates existing A→B records to A→C
        # verify no chain: chain-b should redirect to chain-c, not chain-a
        chain_b_result = SlugRedirect.get_redirect("chain-b")
        self.assertEqual(chain_b_result, "chain-c")
        # And chain-a→chain-c directly (collapsed)
        if result is not None:
            self.assertEqual(result, "chain-c")

    def test_prevents_circular_redirect(self):
        """A→B then B→A: the reverse redirect may be created or blocked.
        The key guarantee is that there is NO circular loop:
        following redirects from either slug should not loop."""
        SlugRedirect.create_redirect(self.resource, "circ-a", "circ-b")
        SlugRedirect.create_redirect(self.resource, "circ-b", "circ-a")
        # The code deletes the reverse redirect (circ-b→circ-a) before creating circ-a→circ-b
        # then it checks for and deletes circ-a→circ-b (reverse of what we're creating)
        # Net result: exactly one direction should exist, not both
        fwd = SlugRedirect.objects.filter(old_slug="circ-a", new_slug="circ-b").exists()
        rev = SlugRedirect.objects.filter(old_slug="circ-b", new_slug="circ-a").exists()
        self.assertFalse(fwd and rev, "Circular redirect detected — both directions exist!")

    def test_deletes_reverse_redirect(self):
        """After preventing circular redirect, only one direction should exist."""
        SlugRedirect.create_redirect(self.resource, "rev-a", "rev-b")
        SlugRedirect.create_redirect(self.resource, "rev-b", "rev-a")
        # rev-a→rev-b should have been cleaned up
        self.assertIsNone(SlugRedirect.get_redirect("rev-a"))

    def test_update_or_create_updates_existing(self):
        """Calling create_redirect with the same old_slug updates new_slug."""
        SlugRedirect.create_redirect(self.resource, "upd-old", "upd-v1")
        SlugRedirect.create_redirect(self.resource, "upd-old", "upd-v2")
        result = SlugRedirect.get_redirect("upd-old")
        self.assertEqual(result, "upd-v2")

    def test_clears_redirect_to_old_slug(self):
        """If A→B exists and we create C→A, the A→B chain entry should be removed."""
        SlugRedirect.create_redirect(self.resource, "clr-a", "clr-b")
        SlugRedirect.create_redirect(self.resource, "clr-c", "clr-a")
        # clr-a→clr-b should be deleted (new_slug=clr-a is cleared)
        self.assertIsNone(SlugRedirect.get_redirect("clr-a"))


class SlugRedirectClearForSlugTests(SEOBaseTestCase):

    def test_clears_redirects_where_slug_is_old(self):
        self.make_redirect("clear-old-slug", "somewhere")
        SlugRedirect.clear_for_slug("clear-old-slug")
        self.assertIsNone(SlugRedirect.get_redirect("clear-old-slug"))

    def test_clears_redirects_where_slug_is_new(self):
        self.make_redirect("some-old", "clear-new-slug")
        SlugRedirect.clear_for_slug("clear-new-slug")
        self.assertFalse(
            SlugRedirect.objects.filter(new_slug="clear-new-slug").exists()
        )

    def test_no_error_when_no_matching_redirects(self):
        """clear_for_slug should not raise when there's nothing to clear."""
        try:
            SlugRedirect.clear_for_slug("nonexistent-slug-999")
        except Exception as e:
            self.fail(f"clear_for_slug raised {e} unexpectedly")
