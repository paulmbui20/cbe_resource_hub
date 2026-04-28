"""
cms/tests/test_context_processors.py

Tests for cms/context_processors.py  — global_settings().

Covers:
  - site_settings dict is injected into every template context
  - menus dict is injected into every template context
  - Values match what's in the DB
  - Cache is populated after first call
  - Empty menus dict is not cached (so new menus appear without TTL wait)
  - Invalidation: after cache is cleared, fresh data is fetched
"""

from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings

from cms.context_processors import (
    _MENUS_CACHE_KEY,
    _SETTINGS_CACHE_KEY,
    global_settings,
)
from cms.models import Menu, SiteSetting
from cms.tests.base import CMSBaseTestCase


class GlobalSettingsContextProcessorTests(CMSBaseTestCase):
    """Tests that exercise global_settings() directly via the RequestFactory."""

    def setUp(self):
        super().setUp()
        cache.clear()
        self.request = RequestFactory().get("/")

    def tearDown(self):
        cache.clear()

    # ── site_settings ─────────────────────────────────────────────────────────

    def test_site_settings_key_is_in_context(self):
        ctx = global_settings(self.request)
        self.assertIn("site_settings", ctx)

    def test_site_settings_is_a_dict(self):
        ctx = global_settings(self.request)
        self.assertIsInstance(ctx["site_settings"], dict)

    def test_site_settings_contains_expected_keys(self):
        ctx = global_settings(self.request)
        ss = ctx["site_settings"]
        self.assertIn("site_name", ss)
        self.assertIn("contact_email", ss)
        self.assertIn("contact_phone", ss)

    def test_site_settings_values_match_db(self):
        ctx = global_settings(self.request)
        self.assertEqual(ctx["site_settings"]["site_name"], "Test Site Name")
        self.assertEqual(ctx["site_settings"]["contact_email"], "contact@example.com")

    def test_site_settings_cached_after_first_call(self):
        global_settings(self.request)
        cached = cache.get(_SETTINGS_CACHE_KEY)
        self.assertIsNotNone(cached)
        self.assertIn("site_name", cached)

    def test_site_settings_served_from_cache_on_second_call(self):
        # Pre-populate cache with known data
        cache.set(_SETTINGS_CACHE_KEY, {"injected_key": "injected_value"}, 60)
        ctx = global_settings(self.request)
        # Should return cached data, not DB data
        self.assertEqual(ctx["site_settings"].get("injected_key"), "injected_value")

    def test_site_settings_refreshed_after_cache_cleared(self):
        global_settings(self.request)
        cache.delete(_SETTINGS_CACHE_KEY)
        # New setting added between calls
        SiteSetting.objects.create(key="fresh_key_001", value="fresh_value")
        ctx = global_settings(self.request)
        self.assertIn("fresh_key_001", ctx["site_settings"])

    # ── menus ─────────────────────────────────────────────────────────────────

    def test_menus_key_is_in_context(self):
        ctx = global_settings(self.request)
        self.assertIn("menus", ctx)

    def test_menus_is_a_dict(self):
        ctx = global_settings(self.request)
        self.assertIsInstance(ctx["menus"], dict)

    def test_menus_keys_are_slugified_names(self):
        ctx = global_settings(self.request)
        # "Primary Header" → "primary_header", "Footer" → "footer"
        self.assertIn("primary_header", ctx["menus"])
        self.assertIn("footer", ctx["menus"])

    def test_menus_values_are_menu_instances(self):
        from cms.models import Menu as MenuModel
        ctx = global_settings(self.request)
        for v in ctx["menus"].values():
            self.assertIsInstance(v, MenuModel)

    def test_menus_cached_after_first_call(self):
        global_settings(self.request)
        cached = cache.get(_MENUS_CACHE_KEY)
        self.assertIsNotNone(cached)

    def test_menus_served_from_cache_on_second_call(self):
        # Pre-seed cache with sentinel
        sentinel_menu = Menu.objects.create(name="Cached Menu Only")
        cache.set(_MENUS_CACHE_KEY, {"cached_menu_only": sentinel_menu}, 60)
        ctx = global_settings(self.request)
        self.assertIn("cached_menu_only", ctx["menus"])

    def test_empty_menus_not_cached(self):
        """
        When there are no menus in the DB the result must NOT be cached
        so that newly created menus appear immediately on the next request.
        """
        # Use a clean test DB state with no menus
        Menu.objects.all().delete()
        cache.delete(_MENUS_CACHE_KEY)
        global_settings(self.request)
        cached = cache.get(_MENUS_CACHE_KEY)
        self.assertIsNone(cached)

    def test_menus_refreshed_after_cache_cleared(self):
        global_settings(self.request)
        cache.delete(_MENUS_CACHE_KEY)
        new_menu = Menu.objects.create(name="Dynamic New Menu")
        ctx = global_settings(self.request)
        self.assertIn("dynamic_new_menu", ctx["menus"])


class GlobalSettingsViaClientTests(CMSBaseTestCase):
    """
    Verify that site_settings and menus land in the template context
    when rendering a real view (PageDetailView).
    """

    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_site_settings_in_template_context(self):
        from django.urls import reverse
        response = self.client.get(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))
        self.assertIn("site_settings", response.context)

    def test_menus_in_template_context(self):
        from django.urls import reverse
        response = self.client.get(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))
        self.assertIn("menus", response.context)
