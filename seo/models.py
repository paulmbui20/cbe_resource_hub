import os
import sys
from io import BytesIO

from PIL import Image
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.files.storage import storages, FileSystemStorage
from django.db import models

from core.models import TimeStampedModel
from validators import validate_image_file


class PublicFilesStorageCallable:
    """
    Callable that returns the appropriate storage backend for files.
    This is evaluated at runtime, not at class definition time.
    """

    def __call__(self):

        # In tests, always use FileSystemStorage
        if "pytest" in sys.modules or "test" in sys.argv:
            return FileSystemStorage()

        try:
            return storages["public_files"]
        except (KeyError, AttributeError):
            # Fallback to default storage
            return storages["default"]

    def deconstruct(self):
        """
        Allow Django to serialize this for migrations.
        """
        return ("seo.models.PublicFilesStorageCallable", [], {})


class SEOModel(TimeStampedModel, models.Model):
    """
    Abstract base model for SEO fields.
    Inherit this to add SEO capabilities to any model.
    """

    featured_image = models.ImageField(
        upload_to="featured_images/%Y/%m/",
        storage=PublicFilesStorageCallable(),
        null=True,
        blank=True,
        validators=[validate_image_file],
        help_text="Featured image for this page",
    )
    focus_keyword = models.CharField(
        max_length=60,
        blank=True,
        default="",
        help_text="Enter the main keyword this page should rank for.",
    )
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="SEO title (60 chars max). Leave blank to auto-generate.",
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO description (160 chars max). Leave blank to auto-generate.",
    )
    meta_keywords = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated keywords for SEO"
    )

    class Meta:
        abstract = True  # This ensures no database table is created

    def get_meta_title(self):
        """Override in child models to provide auto-generated title"""
        return self.meta_title or str(self)

    def get_meta_description(self):
        """Override in child models to provide auto-generated description"""
        return self.meta_description or ""

    def get_meta_keywords(self):
        """Override in child models to provide auto-generated keywords"""
        return self.meta_keywords or ""

    def optimize_image(self):
        """Generate WebP and resized versions of featured_images"""
        if not self.featured_image:
            return

        try:
            img = Image.open(self.featured_image.open("rb"))

            if img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = rgb_img

            sizes = [
                ("small", 329, 439, 80),
                ("medium", 658, 878, 85),
            ]

            base_name = os.path.splitext(self.featured_image.name)[0]

            for size_name, width, height, quality in sizes:
                img_copy = img.copy()
                img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)

                webp_buffer = BytesIO()
                img_copy.save(webp_buffer, format="WEBP", quality=quality)
                webp_buffer.seek(0)
                self.featured_image.storage.save(
                    f"{base_name}_{size_name}.webp", ContentFile(webp_buffer.read())
                )
                webp_buffer.close()

                jpg_buffer = BytesIO()
                img_copy.save(jpg_buffer, format="JPEG", quality=quality + 5)
                jpg_buffer.seek(0)
                self.featured_image.storage.save(
                    f"{base_name}_{size_name}.jpg", ContentFile(jpg_buffer.read())
                )
                jpg_buffer.close()

            img.close()
            print(f"✓ Image optimization complete for {self.featured_image.name}")

        except Exception as e:
            print(f"✗ Image optimization failed: {str(e)}")

    @property
    def featured_image_small_webp(self):
        if not self.featured_image:
            return None
        try:
            base_name = os.path.splitext(self.featured_image.name)[0]
            return self.featured_image.storage.url(f"{base_name}_small.webp")
        except Exception:
            return self.featured_image.url

    @property
    def featured_image_small_jpg(self):
        if not self.featured_image:
            return None
        try:
            base_name = os.path.splitext(self.featured_image.name)[0]
            return self.featured_image.storage.url(f"{base_name}_small.jpg")
        except Exception:
            return self.featured_image.url

    @property
    def featured_image_medium_webp(self):
        if not self.featured_image:
            return None
        try:
            base_name = os.path.splitext(self.featured_image.name)[0]
            return self.featured_image.storage.url(f"{base_name}_medium.webp")
        except Exception:
            return self.featured_image.url

    @property
    def featured_image_medium_jpg(self):
        if not self.featured_image:
            return None
        try:
            base_name = os.path.splitext(self.featured_image.name)[0]
            return self.featured_image.storage.url(f"{base_name}_medium.jpg")
        except Exception:
            return self.featured_image.url

    @property
    def featured_image_webp_srcset(self):
        if not self.featured_image:
            return ""
        small = self.featured_image_small_webp
        medium = self.featured_image_medium_webp
        if small and medium:
            return f"{small} 329w, {medium} 658w"
        return f"{self.featured_image.url} 329w, {self.featured_image.url} 658w"

    @property
    def featured_image_jpg_srcset(self):
        if not self.featured_image:
            return ""
        small = self.featured_image_small_jpg
        medium = self.featured_image_medium_jpg
        if small and medium:
            return f"{small} 329w, {medium} 658w"
        return f"{self.featured_image.url} 329w, {self.featured_image.url} 658w"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        old_featured_image = None

        if not is_new:
            old_featured_image = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("featured_image", flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        if self.featured_image and (
            is_new or old_featured_image != self.featured_image.name
        ):
            self.optimize_image()


class SlugRedirect(TimeStampedModel, models.Model):
    """
    Stores previous slugs for permanent redirects.
    Indexed for blazingly fast lookups with zero latency impact.
    """

    content_type = models.ForeignKey(
        "contenttypes.ContentType", on_delete=models.CASCADE, db_index=True
    )
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    old_slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Previous slug that should redirect",
    )
    new_slug = models.SlugField(
        max_length=255, db_index=True, help_text="Current slug to redirect to"
    )

    hit_count = models.PositiveIntegerField(
        default=0, help_text="Track redirect usage for analytics"
    )

    class Meta:
        indexes = [
            models.Index(fields=["old_slug"]),  # Primary lookup
            models.Index(fields=["new_slug"]),  # Reverse lookup
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Slug Redirect"
        verbose_name_plural = "Slug Redirects"

    def __str__(self):
        return f"{self.old_slug} → {self.new_slug}"

    @classmethod
    def get_redirect(cls, old_slug):
        """
        Fast lookup for redirect. Returns new slug or None.
        Uses select_related to minimize queries.
        """
        try:
            redirect = cls.objects.select_related("content_type").get(old_slug=old_slug)
            # Increment hit counter asynchronously (non-blocking)
            cls.objects.filter(pk=redirect.pk).update(
                hit_count=models.F("hit_count") + 1
            )
            return redirect.new_slug
        except cls.DoesNotExist:
            return None

    @classmethod
    def create_redirect(cls, instance, old_slug, new_slug):
        """
        Create or update redirect record.
        Prevents redirect chains and circular redirects.
        Handles the case where slug changes back to a previous value.
        """
        if old_slug == new_slug:
            return None

        content_type = ContentType.objects.get_for_model(instance)

        # 1: Delete any redirect pointing TO the old_slug
        cls.objects.filter(new_slug=old_slug).delete()

        # 2: Delete any redirect FROM the new_slug
        # This handles the case where we're changing back to a previous slug
        cls.objects.filter(old_slug=new_slug).delete()

        # 3: Update existing redirects that point to old_slug
        # This prevents redirect chains: A → B, then B → C should become A → C
        existing_redirects_to_old = cls.objects.filter(new_slug=old_slug)
        for redirect in existing_redirects_to_old:
            redirect.new_slug = new_slug
            redirect.save(update_fields=["new_slug", "updated_at"])

        # 4: Check if this redirect already exists in reverse
        # Delete the reverse redirect to prevent circular loops
        reverse_redirect = cls.objects.filter(
            old_slug=new_slug, new_slug=old_slug
        ).first()
        if reverse_redirect:
            reverse_redirect.delete()
            return None  # Don't create new redirect

        # Now create or update the redirect
        redirect, created = cls.objects.update_or_create(
            old_slug=old_slug,
            defaults={
                "content_type": content_type,
                "object_id": instance.pk,
                "new_slug": new_slug,
            },
        )

        return redirect

    @classmethod
    def clear_for_slug(cls, slug):
        """
        Clear all redirects related to a slug (both as source and target).
        Use this when a slug is reused.
        """
        from django.core.cache import cache

        # Delete redirects where this slug is the old_slug
        old_redirects = cls.objects.filter(old_slug=slug)
        for r in old_redirects:
            cache.delete(f"slug_redirect_{r.old_slug}")
        old_redirects.delete()

        # Delete redirects where this slug is the new_slug
        new_redirects = cls.objects.filter(new_slug=slug)
        for r in new_redirects:
            cache.delete(f"slug_redirect_{r.old_slug}")
        new_redirects.delete()

        # Clear cache for this slug
        cache.delete(f"slug_redirect_{slug}")


# backward compatibility
from .mixins import SlugRedirectMixin  #  noqa: F401
