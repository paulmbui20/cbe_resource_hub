from datetime import datetime

from django.core.cache import cache

current_year = datetime.now().year


def clear_object_cache(model, slug):
    cache_base_key = f"{model._meta.app_label}:{model._meta.model_name}:{slug}"

    object_instance_cache = cache.get(cache_base_key)
    if object_instance_cache:
        cache.delete(cache_base_key)
