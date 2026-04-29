"""
resources/signals.py

Cache invalidation signals for the resources app.

Each signal handler busts exactly the cache key(s) that are stale when the
corresponding model changes — nothing more, nothing less.
"""

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.utils import clear_object_cache
from resources.models import LearningArea, Grade, EducationLevel, ResourceItem


@receiver([post_save, post_delete], sender=LearningArea)
def clear_learning_areas_cache(sender, instance, **kwargs):
    cache.delete("resources:learning_areas")
    clear_object_cache(LearningArea, instance.slug)


@receiver([post_save, post_delete], sender=Grade)
def clear_grades_cache(sender, instance, **kwargs):
    cache.delete("resources:grades")
    clear_object_cache(Grade, instance.slug)


@receiver([post_save, post_delete], sender=EducationLevel)
def clear_education_levels_cache(sender, instance, **kwargs):
    cache.delete("resources:education_levels")
    clear_object_cache(EducationLevel, instance.slug)


@receiver([post_save, post_delete], sender=ResourceItem)
def clear_home_stats_on_resource_change(sender, instance, **kwargs):
    """
    Bust the homepage stats block whenever a resource is added, updated, or
    deleted — keeps total_resources, total_downloads, and per-type counts fresh.
    """
    from resources.cache import clear_home_stats_cache
    clear_home_stats_cache()
    # Also clear the per-slug object cache for this resource
    if instance.slug:
        clear_object_cache(ResourceItem, instance.slug)
