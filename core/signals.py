from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.models import AcademicSession, Year, Term
from core.utils import clear_object_cache


@receiver([post_save, post_delete], sender=AcademicSession)
def clear_academic_sessions_cache(sender, instance, **kwargs):
    cache_base_key = "resources:academic_sessions"
    cache.delete(cache_base_key)

    model = sender
    slug = instance.slug

    clear_object_cache(model, slug)


@receiver([post_save, post_delete], sender=Term)
def clear_academic_sessions_cache_on_term_change(sender, instance, **kwargs):
    cache_base_key = "resources:academic_sessions"
    cache.delete(cache_base_key)


@receiver([post_save, post_delete], sender=Year)
def clear_academic_sessions_cache_on_year_change(sender, instance, **kwargs):
    cache_base_key = "resources:academic_sessions"
    cache.delete(cache_base_key)
