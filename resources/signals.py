from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from resources.models import LearningArea, Grade, EducationLevel


def clear_object_cache(model, slug):
    cache_base_key = f"{model._meta.app_label}:{model._meta.model_name}:{slug}"

    object_instance_cache = cache.get(cache_base_key)
    if object_instance_cache:
        cache.delete(cache_base_key)


@receiver([post_save, post_delete], sender=LearningArea)
def clear_learning_areas_cache(sender, instance, **kwargs):
    cache_base_key = "resources:learning_areas"
    cache.delete(cache_base_key)

    model = LearningArea
    slug = instance.slug
    clear_object_cache(model, slug)


@receiver([post_save, post_delete], sender=Grade)
def clear_grades_cache(sender, instance, **kwargs):
    cache_base_key = "resources:grades"
    cache.delete(cache_base_key)

    model = Grade
    slug = instance.slug
    clear_object_cache(model, slug)


@receiver([post_save, post_delete], sender=EducationLevel)
def clear_education_levels_cache(sender, instance, **kwargs):
    cache_base_key = "resources:education_levels"
    cache.delete(cache_base_key)

    model = EducationLevel
    slug = instance.slug
    clear_object_cache(model, slug)
