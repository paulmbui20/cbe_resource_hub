from website.models import Partner
from website.models import Testimonial
from django.conf import settings
from django.core.cache import cache
from website.models import FAQ

CACHE_TIMEOUT: int = getattr(settings, "CACHE_TIMEOUT", 3600)


def get_faqs():
    """
    All active FAQs, ordered by order field.
    Invalidated by FAQ.post_save / post_delete signal via ``clear_faqs_cache``.
    """
    key = "website:faqs"
    qs = cache.get(key)
    if qs is None:
        qs = list(FAQ.objects.filter(is_active=True))
        if qs:
            cache.set(key, qs, CACHE_TIMEOUT)
    return qs


def get_testimonials():
    """
    All active testimonials, ordered by order field.
    Invalidated by Testimonial.post_save / post_delete signal via ``clear_testimonials_cache``.
    """
    key = "website:testimonials"
    qs = cache.get(key)
    if qs is None:
        qs = list(Testimonial.objects.filter(is_active=True))
        if qs:
            cache.set(key, qs, CACHE_TIMEOUT)
    return qs


def get_partners():
    """
    All published partners, ordered by order field.
    Invalidated by Partner.post_save / post_delete signal via ``clear_partners_cache``.
    """
    key = "website:partners"
    qs = cache.get(key)
    if qs is None:
        qs = list(Partner.objects.all())
        if qs:
            cache.set(key, qs, CACHE_TIMEOUT)
    return qs
