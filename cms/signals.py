"""
cms/signals.py

Cache invalidation signals — bust the menu/settings caches whenever
a Menu, MenuItem, or SiteSetting is saved or deleted so changes appear
immediately without waiting for the 1-hour cache TTL.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


def _bust_menu_cache(**kwargs):
    from django.core.cache import cache
    cache.delete("cms:menus")


def _bust_settings_cache(**kwargs):
    from django.core.cache import cache
    cache.delete("cms:site_settings")


def register_signals():
    from cms.models import Menu, MenuItem, SiteSetting

    post_save.connect(_bust_menu_cache, sender=Menu)
    post_delete.connect(_bust_menu_cache, sender=Menu)
    post_save.connect(_bust_menu_cache, sender=MenuItem)
    post_delete.connect(_bust_menu_cache, sender=MenuItem)
    post_save.connect(_bust_settings_cache, sender=SiteSetting)
    post_delete.connect(_bust_settings_cache, sender=SiteSetting)
