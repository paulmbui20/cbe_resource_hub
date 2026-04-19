"""
cms/context_processors.py

Injects global CMS data (site settings + navigation menus) into every
template context. Values are cached for a ttl specified in `CACHE_TIMEOUT` in settings.py to avoid
hammering the database on every page load.

Register in settings.py → TEMPLATES[0]['OPTIONS']['context_processors']:
    'cms.context_processors.global_settings',
"""
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.cache import cache

# Cache keys
_SETTINGS_CACHE_KEY = "cms:site_settings"
_MENUS_CACHE_KEY = "cms:menus"
_CACHE_TIMEOUT = getattr(settings, "CACHE_TIMEOUT")


def global_settings(request) -> dict[str, Any]:
    """
    Context processor that makes the following available in all templates:

    - ``site_settings``: dict mapping every SiteSetting key → value
                         e.g. {{ site_settings.site_name }}
    - ``menus``: dict keyed by slug-name for each Menu, with prefetched items
                 e.g. {% for item in menus.primary_header.items.all %}

    Both values are fetched once and cached for 1 hour.
    An empty menus dict is NEVER cached so that newly created menus appear
    immediately without waiting for cache expiry.
    """
    # ------------------------------------------------------------------ #
    # Site Settings
    # ------------------------------------------------------------------ #
    site_settings: dict[str, str] | None = cache.get(_SETTINGS_CACHE_KEY)

    if site_settings is None:
        from cms.models import SiteSetting

        site_settings = dict(SiteSetting.objects.values_list("key", "value"))
        cache.set(_SETTINGS_CACHE_KEY, site_settings, _CACHE_TIMEOUT)

    # ------------------------------------------------------------------ #
    # Navigation Menus
    # ------------------------------------------------------------------ #
    menus: dict[str, Any] | None = cache.get(_MENUS_CACHE_KEY)

    if menus is None:
        from cms.models import Menu

        # Prefetch items (and their children) to prevent N+1 queries.
        menu_qs = list(
            Menu.objects.prefetch_related(
                "items",
                "items__children",
                "items__parent",
            )
        )
        # Build a slug-keyed dict so templates can do {{ menus.primary_header }}
        menus = {
            menu.name.lower().replace(" ", "_"): menu for menu in menu_qs
        }
        # Only cache if we actually have menus; otherwise re-query next request
        # so newly created menus show up without waiting for TTL expiry.
        if menus:
            cache.set(_MENUS_CACHE_KEY, menus, _CACHE_TIMEOUT)

    return {
        "site_settings": site_settings,
        "menus": menus,
    }
