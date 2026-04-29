from django.db import models


def slug_to_title(slug: str) -> str:
    slug = slug
    if "-" in slug:
        slug = slug.replace("-", " ")
    if "_" in slug:
        slug = slug.replace("_", " ")
    slug = slug.title()
    return slug


def unique_slug_generator(slug: str, max_length: int, model: models.Model) -> str:
    candidate = slug[:max_length - 2]
    if not model.objects.filter(slug=candidate).exists():
        return candidate
    counter = 1
    while model.objects.filter(slug=f"{candidate}-{counter}").exists():
        counter += 1
    return f"{slug}-{counter}"
