from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet, Model
from django.shortcuts import get_object_or_404

from core.models import AcademicSession
from resources.models import LearningArea, Grade, ResourceItem, EducationLevel

CACHE_TIMEOUT = getattr(settings, "CACHE_TIMEOUT")


def get_learning_areas() -> QuerySet[LearningArea]:
    """
    Returns the learning areas from the cache if it exists,
    otherwise queries the database returns the result and caches it for later use.
    """
    cache_base_key = "resources:learning_areas"
    learning_areas = cache.get(cache_base_key)
    if not learning_areas:
        learning_areas = LearningArea.objects.all().prefetch_related("resources")
        if learning_areas.exists():
            cache.set(cache_base_key, learning_areas, CACHE_TIMEOUT)
    return learning_areas


def get_grades() -> QuerySet[Grade]:
    """
    Returns the grades from the cache if it exists,
    otherwise queries the database returns the result and caches it for later use.
    """
    cache_base_key = "resources:grades"
    grades = cache.get(cache_base_key)
    if not grades:
        grades = Grade.objects.all().prefetch_related("resources")
        if grades.exists():
            cache.set(cache_base_key, grades, CACHE_TIMEOUT)
    return grades


def get_resource_types() -> dict[str, str]:
    """
    Returns a dictionary of resource_types from the cache if it exists,
    otherwise queries the database returns the result and caches it for later use.
    """
    cache_base_key = "resources:resource_types"
    resource_types = cache.get(cache_base_key)
    if not resource_types:
        resource_types = dict(ResourceItem._meta.get_field("resource_type").choices)
        if resource_types.keys():
            cache.set(cache_base_key, resource_types, CACHE_TIMEOUT)
    return resource_types


def get_education_levels() -> QuerySet[EducationLevel]:
    """
    Returns a queryset of education_levels from the cache if it exists,
    otherwise queries the database returns the result and caches it for later use.
    """
    cache_base_key = "resources:education_levels"
    education_levels = cache.get(cache_base_key)
    if not education_levels:
        education_levels = EducationLevel.objects.all().prefetch_related("grades")
        if education_levels.exists():
            cache.set(cache_base_key, education_levels, CACHE_TIMEOUT)
    return education_levels


def get_slug_based_object_or_404_with_cache(model: Model, slug: str):
    """
    Returns an object based on slug and model from the cache if it exists,
    otherwise queries the database returns the result and caches it for later use.
    """
    cache_base_key = f"{model._meta.app_label}:{model._meta.model_name}:{slug}"

    _object = cache.get(cache_base_key)

    if not _object:
        _object = get_object_or_404(model, slug=slug)
        if _object:
            cache.set(cache_base_key, _object, CACHE_TIMEOUT)
    return _object


def get_academic_sessions() -> QuerySet[AcademicSession]:
    cache_base_key = "resources:academic_sessions"
    academic_sessions = cache.get(cache_base_key)
    if not academic_sessions:
        academic_sessions = AcademicSession.objects.all().prefetch_related("resources")
        if academic_sessions.exists():
            cache.set(cache_base_key, academic_sessions, CACHE_TIMEOUT)
    return academic_sessions
