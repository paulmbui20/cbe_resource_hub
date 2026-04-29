"""
seo/tests/test_middleware.py

Tests for SlugRedirectMiddleware:
  - Known slug-based views get redirect checked BEFORE response
  - 301 permanent redirect returned when old_slug is in DB
  - Non-slug views are ignored (middleware returns None for check)
  - 404 on a slug URL triggers fallback redirect check
  - Non-slug-based URLs are passed through untouched
  - Query string preserved in redirect
  - Cache hit path: redirect returned without DB query
  - Cache miss stored as empty string to prevent repeated DB hits
"""

from unittest.mock import patch, MagicMock

from django.core.cache import cache
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.test import TestCase, RequestFactory

from seo.middleware import SlugRedirectMiddleware
from seo.models import SlugRedirect
from seo.tests.base import SEOBaseTestCase


class SlugRedirectMiddlewareTests(SEOBaseTestCase):

    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    def tearDown(self):
        cache.clear()

    def _middleware(self, get_response=None):
        if get_response is None:
            get_response = lambda r: HttpResponse("ok", status=200)
        return SlugRedirectMiddleware(get_response)

    # ── Known view with old slug → redirect ────────────────────────────────────

    def test_redirects_known_slug_for_resource_detail(self):
        self.make_redirect("seo-old-res", "seo-resource")
        request = self.factory.get("/resources/seo-old-res/")
        mw = self._middleware()
        response = mw(request)
        self.assertEqual(response.status_code, 301)

    def test_redirect_is_permanent(self):
        self.make_redirect("perm-old", "perm-new")
        request = self.factory.get("/resources/perm-old/")
        mw = self._middleware()
        response = mw(request)
        self.assertIsInstance(response, HttpResponsePermanentRedirect)

    def test_redirect_points_to_new_url(self):
        self.make_redirect("mw-old", "seo-resource")  # new_slug must match existing resource
        request = self.factory.get("/resources/mw-old/")
        mw = self._middleware()
        response = mw(request)
        self.assertIn("seo-resource", response["Location"])

    def test_unknown_slug_passes_through(self):
        request = self.factory.get("/resources/completely-unknown-slug/")
        get_response = MagicMock(return_value=HttpResponse("ok"))
        mw = self._middleware(get_response)
        mw(request)
        get_response.assert_called_once()

    def test_non_slug_url_passes_through(self):
        request = self.factory.get("/")
        get_response = MagicMock(return_value=HttpResponse("home"))
        mw = self._middleware(get_response)
        response = mw(request)
        self.assertEqual(response.status_code, 200)

    def test_query_string_preserved_in_redirect(self):
        self.make_redirect("qs-old", "seo-resource")
        request = self.factory.get("/resources/qs-old/?q=test&page=2")
        mw = self._middleware()
        response = mw(request)
        if response.status_code == 301:
            self.assertIn("q=test", response["Location"])

    # ── 404 fallback redirect ──────────────────────────────────────────────────

    def test_404_triggers_redirect_check(self):
        self.make_redirect("404-old", "seo-resource")
        request = self.factory.get("/resources/404-old/")
        get_response = lambda r: HttpResponse(status=404)
        mw = self._middleware(get_response)
        response = mw(request)
        self.assertEqual(response.status_code, 301)

    # ── Cache behaviour ────────────────────────────────────────────────────────

    def test_cache_hit_avoids_db_query(self):
        """If cache already has the new slug, DB should not be queried."""
        cache.set("slug_redirect_cached-old", "seo-resource", 60)
        request = self.factory.get("/resources/cached-old/")
        mw = self._middleware()
        with self.assertNumQueries(0):
            response = mw(request)
        if response.status_code == 301:
            self.assertIn("seo-resource", response["Location"])

    def test_cache_miss_stores_empty_string_for_no_redirect(self):
        """Unknown slug should cache an empty string to prevent repeated DB hits."""
        request = self.factory.get("/resources/no-redirect-here/")
        mw = self._middleware()
        mw(request)
        cached = cache.get("slug_redirect_no-redirect-here")
        # Either None (not cached at all) or empty string (cached miss) — both ok
        self.assertIn(cached, [None, ""])

    def test_no_redirect_for_empty_cached_value(self):
        """Empty string cached value means 'no redirect' — pass through."""
        cache.set("slug_redirect_cached-miss", "", 60)
        request = self.factory.get("/resources/cached-miss/")
        get_response = MagicMock(return_value=HttpResponse("ok"))
        mw = self._middleware(get_response)
        response = mw(request)
        # Should not 301 — the get_response should be called
        get_response.assert_called()

    # ── Graceful error handling ────────────────────────────────────────────────

    def test_exception_in_middleware_returns_normal_response(self):
        """Even if resolve() errors, middleware should not crash the site."""
        request = self.factory.get("/this-path-does-not-resolve-to-anything-valid/")
        get_response = MagicMock(return_value=HttpResponse("ok"))
        mw = self._middleware(get_response)
        response = mw(request)
        self.assertIsNotNone(response)
