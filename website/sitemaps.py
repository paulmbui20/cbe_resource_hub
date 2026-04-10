"""
website/sitemaps.py

Sitemap classes for all public-facing content.
Compatible with Google Search Console XML sitemap protocol.
"""
from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from cms.models import Page
from resources.models import ResourceItem
from website.models import Partner


class StaticViewSitemap(Sitemap):
    """Static public pages that don't come from the database."""
    priority = 1.0
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return ["home", "contact", "partners"]

    def location(self, item):
        return reverse(item)


class PageSitemap(Sitemap):
    """CMS Pages — only published ones."""
    priority = 0.8
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return Page.objects.filter(is_published=True).only("slug", "updated_at")

    def location(self, obj):
        from django.urls import reverse as r
        return r("cms:page_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class ResourceSitemap(Sitemap):
    """All ResourceItems (free + premium — both are indexable)."""
    priority = 0.9
    changefreq = "daily"
    protocol = "https"

    def items(self):
        return ResourceItem.objects.all().only("slug", "updated_at").order_by("-created_at")

    def location(self, obj):
        from django.urls import reverse as r
        return r("resources:detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class PartnerSitemap(Sitemap):
    """Public partner entries."""
    priority = 0.5
    changefreq = "monthly"
    protocol = "https"

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
}
