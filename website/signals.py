from core.utils import clear_object_cache
from website.models import Partner
from website.models import Testimonial
from django.dispatch import receiver
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from website.models import FAQ


@receiver([post_save, post_delete], sender=FAQ)
def clear_faqs_cache(sender, instance, **kwargs):
    cache.delete("website:faqs")


@receiver([post_save, post_delete], sender=Testimonial)
def clear_testimonials_cache(sender, instance, **kwargs):
    cache.delete("website:testimonials")


@receiver([post_save, post_delete], sender=Partner)
def clear_partners_cache(sender, instance, **kwargs):
    cache.delete("website:partners")

    model = sender
    slug = instance.slug
    clear_object_cache(model, slug)
