from django.core.cache import cache
from django.db import models


class SlugRedirectMixin(models.Model):
    """
    Mixin to automatically track slug changes and create redirects.
    Add this to any model that uses slugs for URLs.

    Handles:
    - Redirect creation
    - Circular redirect prevention
    - Redirect chain prevention
    - Cache invalidation

    Usage:
        class YourModel(SlugRedirectMixin, models.Model):
            slug = models.SlugField(...)
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Override save to track slug changes"""
        # Check if this is an update and slug has changed
        if self.pk:
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)
                old_slug = old_instance.slug
                new_slug = self.slug

                # If slug changed, handle redirects
                if old_slug and new_slug and old_slug != new_slug:
                    # CRITICAL: Clear any existing redirects for the new slug
                    # This handles the case where we're changing BACK to a previous slug
                    from .models import SlugRedirect
                    SlugRedirect.clear_for_slug(new_slug)

                    # Create the redirect (this handles chain prevention internally)
                    SlugRedirect.create_redirect(
                        instance=self,
                        old_slug=old_slug,
                        new_slug=new_slug
                    )

                    # Clear ALL caches for both old and new slugs
                    self._clear_all_slug_caches(old_slug)
                    self._clear_all_slug_caches(new_slug)

            except self.__class__.DoesNotExist:
                pass  # Object doesn't exist yet, skip redirect creation

        super().save(*args, **kwargs)

        # Clear cache for new slug after save
        if hasattr(self, 'slug') and self.slug:
            self._clear_slug_cache(self.slug)

    def _clear_all_slug_caches(self, slug):
        """
        Clear ALL cache entries for a slug - including redirect cache.
        This is CRITICAL to prevent serving stale redirects.
        """
        from django_redis import get_redis_connection

        # Get model name and app label for cache keys
        model_name = self._meta.model_name
        app_label = self._meta.app_label

        # Clear specific cache keys
        cache_keys = [
            f'slug_redirect_{slug}',  # CRITICAL: Clear redirect cache
            f"{app_label}:{model_name}:{slug}",
        ]
        cache.delete_many(cache_keys)

        # Clear all pattern-based caches for this slug using Redis
        try:
            redis_conn = get_redis_connection("default")
            patterns = [
                f":1:*{slug}*",  # Any cache key containing this slug
            ]

            all_keys = []
            for pattern in patterns:
                keys = redis_conn.keys(pattern)
                if keys:
                    all_keys.extend(keys)

            if all_keys:
                redis_conn.delete(*all_keys)
        except Exception as e:
            import logging
            logging.error(f"Error clearing Redis cache for slug {slug}: {e}")

        # Call the custom cache clear method
        self._clear_slug_cache(slug)

    def _clear_slug_cache(self, slug):
        """
        Clear cache entries for this slug.
        Override this method in your model for custom cache clearing.
        """
        # Get model name and app label for cache keys
        model_name = self._meta.model_name
        app_label = self._meta.app_label

        # Clear specific cache keys
        cache_keys = [
            f'slug_redirect_{slug}',  # CRITICAL: Clear redirect cache
            f"{app_label}:{model_name}:{slug}",
        ]

        cache.delete_many(cache_keys)
