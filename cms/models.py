"""
cms/models.py

WordPress-like dynamic CMS functionality:
- SiteSetting: global key/value config store
- Menu & MenuItem: navigation structure with self-referential hierarchy
- Page: static CMS pages with slug-based routing
"""

from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import slugify
from tinymce.models import HTMLField

from cms.utils import unique_slug_generator
from seo.models import SlugRedirectMixin, SEOModel


class SiteSetting(models.Model):
    """
    Global key/value store for site-wide settings.

    Examples:
        SiteSetting.objects.get(key="site_name").value
        SiteSetting.objects.get(key="support_email").value
        SiteSetting.objects.get(key="meta_description").value
    """

    key: str = models.CharField(
        max_length=50,
        db_index=True,
        help_text='Setting identifier (e.g. "site_name", "contact_email", "contact_phone", "site_indexing").',
    )
    value: str = models.TextField(
        help_text="The value for this setting. (e.g. 'CBE Resources Hub', 'info@example.com', '+254712345678', 'true')",
    )

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"
        ordering = ["key"]
        constraints = [
            models.UniqueConstraint(
                Lower("key"),
                name="unique_site_setting_key",
                violation_error_message="Site Setting key must be unique"
            )
        ]

    def __str__(self) -> str:
        return f"{self.key} = {self.value[:60]}"


class MenuManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset().prefetch_related(
                "items", "items__parent", "items__children", "items__parent__parent",
            )
        )


class Menu(models.Model):
    """
    A named navigation menu container (e.g. "Primary Header", "Footer").
    """

    name: str = models.CharField(
        max_length=50,
        help_text='Human-readable menu name (e.g. "Primary Header", "Footer").',
    )

    objects = MenuManager()

    class Meta:
        verbose_name = "Menu"
        verbose_name_plural = "Menus"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_menu_name",
                violation_error_message="Menu name must be unique"
            )
        ]

    def __str__(self) -> str:
        return self.name


class MenuItemsManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset().select_related(
                "menu", "parent", "parent__parent", "parent__menu", "parent__parent__parent",
            )
        )


class MenuItem(models.Model):
    """
    A single navigation item inside a Menu.

    Supports hierarchical structure via a self-referential parent FK,
    allowing unlimited nesting depth (mega-menus, dropdowns, etc.).
    """

    menu: Menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name="items",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent item for nested/dropdown menus.",
    )
    title: str = models.CharField(max_length=100)
    url: str = models.CharField(
        max_length=500,
        help_text="Absolute URL, relative path, or named URL pattern.",
    )
    order: int = models.PositiveIntegerField(
        default=0,
        help_text="Display order within the same level (lower = earlier).",
    )

    objects = MenuItemsManager()

    class Meta:
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"
        ordering = ["menu", "order", "title"]

    def __str__(self) -> str:
        prefix = f"↳ {self.parent.title} › " if self.parent else ""
        return f"[{self.menu.name}] {prefix}{self.title}"


class Page(SEOModel, SlugRedirectMixin, models.Model):
    """
    A static CMS page served at /pages/<slug>/.

    The `content` field is intentionally a plain TextField so that a rich-text
    editor (e.g. TinyMCE via django-tinymce) can be plugged in at the form
    layer without requiring a model migration.
    """
    title: str = models.CharField(max_length=200)
    slug: str = models.SlugField(
        unique=True,
        db_index=True,
        max_length=200,
        help_text="URL-friendly identifier — auto-populated from the title.",
    )
    content: str = HTMLField(
        help_text="Page body — supports HTML (wire up TinyMCE in admin).",
    )
    is_published: bool = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Only published pages are visible to the public.",
    )

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        ordering = ["title"]

    def __str__(self) -> str:
        status = "✓" if self.is_published else "✗"
        return f"[{status}] {self.title}"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            import cms.models
            self.slug = unique_slug_generator(slugify(self.title), 200, cms.models.Page)
        if self.title and not self.meta_title:
            self.meta_title = self.title[:60]
        if self.content and not self.meta_description:
            self.meta_description = strip_tags(self.content)[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("cms:page_detail", kwargs={"slug": self.slug})
