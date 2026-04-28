"""
cms/tests/test_utils.py

Tests for cms/utils.py:
  - slug_to_title: hyphen → space → title-case, underscore → space → title-case
  - unique_slug_generator: no collision, single collision, multiple collisions,
    max_length truncation
"""

from django.test import TestCase

from cms.models import Page
from cms.utils import slug_to_title, unique_slug_generator


class SlugToTitleTests(TestCase):

    def test_hyphens_replaced_with_spaces(self):
        self.assertEqual(slug_to_title("hello-world"), "Hello World")

    def test_underscores_replaced_with_spaces(self):
        self.assertEqual(slug_to_title("hello_world"), "Hello World")

    def test_result_is_title_cased(self):
        self.assertEqual(slug_to_title("my-page-title"), "My Page Title")

    def test_plain_slug_no_separators(self):
        self.assertEqual(slug_to_title("hello"), "Hello")

    def test_mixed_separators_hyphen_wins(self):
        # The function replaces hyphens first, then underscores.
        result = slug_to_title("hello-world_test")
        # After hyphen → space: "hello world_test", then underscore → space: "hello world test"
        self.assertEqual(result, "Hello World Test")

    def test_empty_string(self):
        # Should not raise; Python's str.title() on empty string returns ""
        result = slug_to_title("")
        self.assertEqual(result, "")

    def test_single_word(self):
        self.assertEqual(slug_to_title("resources"), "Resources")


class UniqueSlugGeneratorTests(TestCase):

    def setUp(self):
        # We create pages directly so we can control slug collisions.
        self.page1 = Page.objects.create(title="Existing Page", slug="existing-page")

    def test_no_collision_returns_slug_as_is(self):
        result = unique_slug_generator("brand-new-slug", 200, Page)
        self.assertEqual(result, "brand-new-slug")

    def test_single_collision_appends_dash_1(self):
        result = unique_slug_generator("existing-page", 200, Page)
        self.assertEqual(result, "existing-page-1")

    def test_multiple_collisions_increments_counter(self):
        Page.objects.create(title="P2", slug="existing-page-1")
        Page.objects.create(title="P3", slug="existing-page-2")
        result = unique_slug_generator("existing-page", 200, Page)
        self.assertEqual(result, "existing-page-3")

    def test_max_length_truncates_candidate(self):
        # max_length=12 → candidate = slug[:10] (max_length - 2)
        long_slug = "a" * 20
        result = unique_slug_generator(long_slug, 12, Page)
        self.assertEqual(result, "a" * 10)

    def test_max_length_truncated_candidate_with_collision(self):
        truncated = "b" * 8  # max_length=10 → candidate = slug[:8]
        Page.objects.create(title="Collision", slug=truncated)
        long_slug = "b" * 20
        result = unique_slug_generator(long_slug, 10, Page)
        self.assertEqual(result, f"{'b' * 20}-1")

    def test_returns_string(self):
        result = unique_slug_generator("test-slug", 200, Page)
        self.assertIsInstance(result, str)
