"""
website/sitemaps.py

Sitemap classes for all public-facing content.
Compatible with Google Search Console XML sitemap protocol.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import Max
from django.urls import reverse

from cms.models import Page
from resources.models import ResourceItem, Grade, LearningArea, EducationLevel
from website.models import Partner


class StaticViewSitemap(Sitemap):
    """Static public pages that don't come from the database."""
    priority = 1.0
    changefreq = "weekly"
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        return [
            "home", "contact", "partners",
            "resources:list", "resources:grade_list",
            "resources:learning_areas_list",
        ]

    def location(self, item):
        return reverse(item)


class PageSitemap(Sitemap):
    """CMS Pages — only published ones."""
    priority = 0.8
    changefreq = "weekly"
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        return Page.objects.filter(is_published=True).only("slug", "updated_at")

    def location(self, obj):
        return reverse("cms:page_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class ResourceSitemap(Sitemap):
    """All ResourceItems (free + premium — both are indexable)."""
    priority = 0.9
    changefreq = "daily"
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        return ResourceItem.objects.all().only("slug", "updated_at").order_by("-created_at")

    def location(self, obj):
        return reverse("resources:resource_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class ResourceTypeSitemap(Sitemap):
    """Resource type details sitemap"""
    priority = 0.7
    changefreq = "weekly"
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        RESOURCE_TYPES = [
            key
            for key, label in ResourceItem._meta.get_field("resource_type").choices
        ]

        agg = ResourceItem.objects.values('resource_type').annotate(
            latest_update=Max('updated_at')
        )
        self.type_updates = {
            item['resource_type']: item['latest_update'] for item in agg
        }

        return RESOURCE_TYPES

    def location(self, obj):
        return reverse("resources:type_detail", kwargs={"resource_type": obj})

    def lastmod(self, obj):
        return getattr(self, 'type_updates', {}).get(obj)


class GradeSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        return Grade.objects.all()

    def location(self, obj):
        return reverse("resources:grade_details", kwargs={"grade": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class LearningAreaSitemap(Sitemap):
    priority = 0.5
    changefreq = "weekly"
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        return LearningArea.objects.all()

    def location(self, obj):
        return reverse("resources:learning_area_details", kwargs={"learning_area": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class EducationLevelSitemap(Sitemap):
    priority = 0.4
    changefreq = "weekly"
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        return EducationLevel.objects.all()

    def location(self, obj):
        return reverse("resources:education_level_details", kwargs={"education_level": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class PartnerSitemap(Sitemap):
    """Public partner entries."""
    priority = 0.3
    changefreq = "monthly"
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        return Partner.objects.all().only("id", "name")

    def location(self, obj):
        return reverse("partners")


# Registry used in cbe_res_hub/urls.py
sitemaps = {
    "static": StaticViewSitemap,
    "pages": PageSitemap,
    "resources": ResourceSitemap,
    "partners": PartnerSitemap,
    "resource_types": ResourceTypeSitemap,
    "grades": GradeSitemap,
    "learning_areas": LearningAreaSitemap,
    "education_levels": EducationLevelSitemap,
}
