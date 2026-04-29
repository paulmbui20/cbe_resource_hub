"""
resources/cache.py

Centralised cache helpers for frequently-read, rarely-changing reference data.

Design principles:
- Each helper owns exactly one cache key.
- Signals in resources/signals.py bust those keys on save/delete.
- `prefetch_related("resources")` has been intentionally removed from the
  sidebar helpers (learning_areas, grades, academic_sessions) — callers only
  need the names/slugs for filter UI, not the full reverse relation.  Storing
  the full prefetch in Redis wastes memory and creates subtle staleness bugs
  when resources are added/deleted without the sidebar key being invalidated.
- `get_education_levels` keeps `prefetch_related("grades")` because the
  homepage level-pill UI renders grade counts inside each level.
"""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, QuerySet, Model, Sum
from django.shortcuts import get_object_or_404

from core.models import AcademicSession
from resources.models import LearningArea, Grade, ResourceItem, EducationLevel

CACHE_TIMEOUT: int = getattr(settings, "CACHE_TIMEOUT", 3600)

# ---------------------------------------------------------------------------
# Sidebar / filter helpers
# ---------------------------------------------------------------------------

def get_learning_areas() -> QuerySet[LearningArea]:
    """
    All LearningAreas ordered by name, cached for CACHE_TIMEOUT seconds.
    Invalidated by LearningArea post_save / post_delete signal.
    """
    key = "resources:learning_areas"
    qs = cache.get(key)
    if qs is None:
        qs = LearningArea.objects.only("id", "name", "slug").order_by("name")
        # Evaluate to a list so the cached object is stable (not a lazy QS)
        qs = list(qs)
        if qs:
            cache.set(key, qs, CACHE_TIMEOUT)
    return qs


def get_grades() -> QuerySet[Grade]:
    """
    All Grades with their parent level, ordered by level order then grade order.
    Invalidated by Grade post_save / post_delete signal.
    """
    key = "resources:grades"
    qs = cache.get(key)
    if qs is None:
        qs = list(
            Grade.objects.select_related("level")
            .only("id", "name", "slug", "order", "level__id", "level__name", "level__order")
            .order_by("level__order", "order")
        )
        if qs:
            cache.set(key, qs, CACHE_TIMEOUT)
    return qs


def get_education_levels() -> QuerySet[EducationLevel]:
    """
    All EducationLevels with their child grades, ordered by level order.
    `prefetch_related("grades")` is kept here because the homepage pill UI
    renders grade counts per level.
    Invalidated by EducationLevel post_save / post_delete signal.
    """
    key = "resources:education_levels"
    qs = cache.get(key)
    if qs is None:
        qs = list(
            EducationLevel.objects.prefetch_related("grades").order_by("order")
        )
        if qs:
            cache.set(key, qs, CACHE_TIMEOUT)
    return qs


def get_resource_types() -> dict[str, str]:
    """
    Dict of {resource_type_key: label} derived from model choices.
    Choices are constant — cached until server restart (CACHE_TIMEOUT).
    """
    key = "resources:resource_types"
    rt = cache.get(key)
    if rt is None:
        rt = dict(ResourceItem._meta.get_field("resource_type").choices)
        if rt:
            cache.set(key, rt, CACHE_TIMEOUT)
    return rt


def get_academic_sessions() -> list[AcademicSession]:
    """
    All AcademicSessions with year/term joined, ordered descending.
    Invalidated by AcademicSession post_save / post_delete signal.
    """
    key = "resources:academic_sessions"
    sessions = cache.get(key)
    if sessions is None:
        sessions = list(
            AcademicSession.objects.select_related("current_year", "current_term")
            .order_by("-current_year__year", "-current_term__term_number")
        )
        if sessions:
            cache.set(key, sessions, CACHE_TIMEOUT)
    return sessions


# ---------------------------------------------------------------------------
# Slug-based single-object cache
# ---------------------------------------------------------------------------

def get_slug_based_object_or_404_with_cache(model: type[Model], slug: str):
    """
    Fetch a single model instance by slug, caching the result.
    Cache key: ``<app_label>:<model_name>:<slug>``
    Invalidated by the model's own post_save / post_delete signal via
    ``core.utils.clear_object_cache``.
    """
    key = f"{model._meta.app_label}:{model._meta.model_name}:{slug}"
    obj = cache.get(key)
    if obj is None:
        obj = get_object_or_404(model, slug=slug)
        cache.set(key, obj, CACHE_TIMEOUT)
    return obj


# ---------------------------------------------------------------------------
# Homepage stats block
# ---------------------------------------------------------------------------

HOME_STATS_KEY = "website:home_stats"
# Short TTL — stats are approximate; invalidation signal covers exact busting
HOME_STATS_TTL = min(CACHE_TIMEOUT, 300)  # at most 5 minutes


def get_home_stats() -> dict:
    """
    Returns a dict with all scalar stats needed by the homepage in a single
    DB round-trip (one aggregate query + one GROUP BY query).

    Keys returned:
        total_resources  int
        total_downloads  int
        resource_type_counts  dict[str, int]   {type_key: count, ...}

    Invalidated by the ``clear_home_stats_cache`` signal in resources/signals.py.
    """
    stats = cache.get(HOME_STATS_KEY)
    if stats is None:
        # Single aggregate → total_resources + total_downloads in one query
        agg = ResourceItem.objects.aggregate(
            total=Count("id"),
            downloads=Sum("downloads"),
        )
        # Single GROUP BY → one query for all resource-type counts
        type_counts = dict(
            ResourceItem.objects.filter(is_free=True)
            .values_list("resource_type")
            .annotate(cnt=Count("id"))
            .order_by()          # remove default ordering to allow GROUP BY
            .values_list("resource_type", "cnt")
        )
        stats = {
            "total_resources": agg["total"] or 0,
            "total_downloads": agg["downloads"] or 0,
            "resource_type_counts": type_counts,
        }
        cache.set(HOME_STATS_KEY, stats, HOME_STATS_TTL)
    return stats


def clear_home_stats_cache() -> None:
    """Bust the homepage stats cache key. Called from signals."""
    cache.delete(HOME_STATS_KEY)
