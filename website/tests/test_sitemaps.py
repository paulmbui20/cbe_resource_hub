"""
website/tests/test_sitemaps.py

Tests for all sitemap classes:
  - StaticViewSitemap: items() returns list of URL names, location() returns valid URL
  - PageSitemap: only published pages, location and lastmod
  - ResourceSitemap: all resources, location and lastmod
  - ResourceTypeSitemap: all resource type keys, location
  - GradeSitemap: uses get_grades(), location with slug
  - LearningAreaSitemap: uses get_learning_areas(), location with slug
  - AcademicSessionSitemap: uses get_academic_sessions(), location with slug
  - EducationLevelSitemap: uses get_education_levels(), location with slug
  - PartnerSitemap: all partners, location points to /partners/
  - sitemaps registry has all expected keys
"""

from django.test import TestCase
from django.core.cache import cache
from django.urls import reverse

from cms.models import Page
from website.sitemaps import (
    StaticViewSitemap,
    PageSitemap,
    ResourceSitemap,
    ResourceTypeSitemap,
    GradeSitemap,
    LearningAreaSitemap,
    AcademicSessionSitemap,
    EducationLevelSitemap,
    PartnerSitemap,
    sitemaps,
)
from website.tests.base import WebsiteBaseTestCase


class StaticViewSitemapTests(WebsiteBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_items_returns_list(self):
        sitemap = StaticViewSitemap()
        self.assertIsInstance(sitemap.items(), list)

    def test_items_contains_home(self):
        sitemap = StaticViewSitemap()
        self.assertIn("home", sitemap.items())

    def test_items_contains_contact(self):
        sitemap = StaticViewSitemap()
        self.assertIn("contact", sitemap.items())

    def test_location_returns_valid_url(self):
        sitemap = StaticViewSitemap()
        for item in sitemap.items():
            url = sitemap.location(item)
            self.assertTrue(url.startswith("/"), f"Invalid URL for {item}: {url}")

    def test_priority_is_1(self):
        self.assertEqual(StaticViewSitemap.priority, 1.0)


class PageSitemapTests(WebsiteBaseTestCase):

    def setUp(self):
        cache.clear()
        self.published_page = Page.objects.create(
            title="Published Page",
            content="<p>content</p>",
            is_published=True,
        )
        self.unpublished_page = Page.objects.create(
            title="Unpublished Page",
            content="<p>content</p>",
            is_published=False,
        )

    def tearDown(self):
        cache.clear()

    def test_only_published_pages(self):
        sitemap = PageSitemap()
        items = list(sitemap.items())
        pks = [p.pk for p in items]
        self.assertIn(self.published_page.pk, pks)
        self.assertNotIn(self.unpublished_page.pk, pks)

    def test_location_contains_slug(self):
        sitemap = PageSitemap()
        url = sitemap.location(self.published_page)
        self.assertIn(self.published_page.slug, url)

    def test_lastmod_returns_updated_at(self):
        sitemap = PageSitemap()
        self.assertEqual(sitemap.lastmod(self.published_page), self.published_page.updated_at)


class ResourceSitemapTests(WebsiteBaseTestCase):

    def test_items_contains_resource(self):
        sitemap = ResourceSitemap()
        items = list(sitemap.items())
        self.assertIn(self.resource, items)

    def test_location_contains_slug(self):
        sitemap = ResourceSitemap()
        url = sitemap.location(self.resource)
        self.assertIn(self.resource.slug, url)

    def test_lastmod_returns_updated_at(self):
        sitemap = ResourceSitemap()
        self.assertEqual(sitemap.lastmod(self.resource), self.resource.updated_at)

    def test_priority_is_09(self):
        self.assertEqual(ResourceSitemap.priority, 0.9)


class ResourceTypeSitemapTests(WebsiteBaseTestCase):

    def test_items_returns_list(self):
        sitemap = ResourceTypeSitemap()
        items = sitemap.items()
        self.assertIsInstance(items, list)

    def test_items_contains_notes(self):
        sitemap = ResourceTypeSitemap()
        self.assertIn("notes", sitemap.items())

    def test_location_contains_resource_type(self):
        sitemap = ResourceTypeSitemap()
        url = sitemap.location("notes")
        self.assertIn("notes", url)


class GradeSitemapTests(WebsiteBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_items_contains_grade(self):
        sitemap = GradeSitemap()
        items = list(sitemap.items())
        self.assertIn(self.grade, items)

    def test_location_contains_slug(self):
        sitemap = GradeSitemap()
        url = sitemap.location(self.grade)
        self.assertIn(self.grade.slug, url)

    def test_lastmod_returns_updated_at(self):
        sitemap = GradeSitemap()
        self.assertEqual(sitemap.lastmod(self.grade), self.grade.updated_at)


class LearningAreaSitemapTests(WebsiteBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_items_contains_learning_area(self):
        sitemap = LearningAreaSitemap()
        items = list(sitemap.items())
        self.assertIn(self.learning_area, items)

    def test_location_contains_slug(self):
        sitemap = LearningAreaSitemap()
        url = sitemap.location(self.learning_area)
        self.assertIn(self.learning_area.slug, url)


class AcademicSessionSitemapTests(WebsiteBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_items_contains_session(self):
        sitemap = AcademicSessionSitemap()
        items = list(sitemap.items())
        self.assertIn(self.session, items)

    def test_location_contains_slug(self):
        sitemap = AcademicSessionSitemap()
        url = sitemap.location(self.session)
        self.assertIn(self.session.slug, url)


class EducationLevelSitemapTests(WebsiteBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_items_contains_level(self):
        sitemap = EducationLevelSitemap()
        items = list(sitemap.items())
        self.assertIn(self.level, items)

    def test_location_contains_slug(self):
        sitemap = EducationLevelSitemap()
        url = sitemap.location(self.level)
        self.assertIn(self.level.slug, url)

    def test_lastmod_returns_updated_at(self):
        sitemap = EducationLevelSitemap()
        self.assertEqual(sitemap.lastmod(self.level), self.level.updated_at)


class PartnerSitemapTests(WebsiteBaseTestCase):

    def test_items_contains_partner(self):
        sitemap = PartnerSitemap()
        items = list(sitemap.items())
        pks = [p.pk for p in items]
        self.assertIn(self.partner.pk, pks)

    def test_location_returns_partners_url(self):
        sitemap = PartnerSitemap()
        url = sitemap.location(self.partner)
        self.assertEqual(url, reverse("partners"))


class SitemapsRegistryTests(TestCase):

    def test_registry_has_static(self):
        self.assertIn("static", sitemaps)

    def test_registry_has_pages(self):
        self.assertIn("pages", sitemaps)

    def test_registry_has_resources(self):
        self.assertIn("resources", sitemaps)

    def test_registry_has_partners(self):
        self.assertIn("partners", sitemaps)

    def test_registry_has_resource_types(self):
        self.assertIn("resource_types", sitemaps)

    def test_registry_has_grades(self):
        self.assertIn("grades", sitemaps)

    def test_registry_has_learning_areas(self):
        self.assertIn("learning_areas", sitemaps)

    def test_registry_has_education_levels(self):
        self.assertIn("education_levels", sitemaps)

    def test_registry_has_academic_sessions(self):
        self.assertIn("academic_sessions", sitemaps)

    def test_all_values_are_sitemap_classes(self):
        from django.contrib.sitemaps import Sitemap
        for key, cls in sitemaps.items():
            self.assertTrue(
                issubclass(cls, Sitemap),
                f"sitemaps['{key}'] is not a Sitemap subclass"
            )
