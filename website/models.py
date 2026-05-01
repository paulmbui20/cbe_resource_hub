"""
website/models.py

Stores submitted contact form messages so admins can read and manage
them from the custom management panel.
"""

from django.db import models
from django.db.models.functions import Lower
from django.utils.html import strip_tags
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField
from tinymce.models import HTMLField

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.images.models import AbstractImage, AbstractRendition
from wagtail.documents.models import AbstractDocument

from core.models import TimeStampedModel
from seo.models import SEOModel, SlugRedirectMixin
from validators import validate_image_file


class ContactMessage(models.Model):
    """A message submitted via the public Contact Us form."""

    name = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    phone = PhoneNumberField(
        blank=True,
        null=True,
        default=None,
        help_text="Optional phone number provided by the sender.",
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark as read after the admin has reviewed this message.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self) -> str:
        status = "✓" if self.is_read else "●"
        return f"[{status}] {self.name} — {self.subject}"


class Partner(SEOModel, SlugRedirectMixin, models.Model):
    name = models.CharField(max_length=255)
    link = models.URLField(null=True, blank=True)
    slug = models.SlugField(max_length=255, null=True, blank=True)
    description = HTMLField(null=True, blank=True)
    logo = models.ImageField(
        upload_to="partners/logos/",
        null=True,
        blank=True,
        validators=[validate_image_file],
        help_text="Partner logo image (displayed on listings and banners).",
    )
    show_as_banner = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Show this partner as a banner/ad strip on the public website.",
    )
    banner_cta = models.CharField(
        max_length=80,
        blank=True,
        default="Learn More",
        help_text="Call-to-action button text shown on the banner.",
    )

    def delete(self, using=None, keep_parents=False):
        if self.featured_image:
            self.featured_image.delete(save=False)
        if self.logo:
            self.logo.delete(save=False)
        return super().delete(using=using, keep_parents=keep_parents)

    def save(self, *args, **kwargs):
        if not self.slug or self.slug == "":
            self.slug = slugify(self.name)
        if self.name and not self.meta_title:
            self.meta_title = self.name
        if self.description and not self.meta_description:
            self.meta_description = strip_tags(self.description)
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.name} Partner on URL {self.link} added on {self.created_at}"
            if self.link
            else f"{self.name} Partner"
        )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_partner_name",
                violation_error_message="Partner with this name already exists",
            ),
            models.UniqueConstraint(
                fields=["link"],
                name="unique_partner_url",
                violation_error_message="Partner with this url already exists",
                condition=models.Q(link__isnull=False),
            ),
        ]


class EmailSubscriber(TimeStampedModel, models.Model):
    full_name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(unique=True)
    opted_out = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Email Subscriber"
        verbose_name_plural = "Email Subscribers"
        ordering = ["-created_at"]


# ──────────────────────────────────────────────────────────────────────────────
# WAGTAIL BLOG & MEDIA MODELS
# ──────────────────────────────────────────────────────────────────────────────


class CustomImage(AbstractImage):
    file = models.ImageField(
        upload_to="wagtail_images/", storage="public_files", verbose_name="file"
    )


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(
        CustomImage, on_delete=models.CASCADE, related_name="renditions"
    )
    file = models.ImageField(upload_to="wagtail_renditions/", storage="public_files")

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)


class CustomDocument(AbstractDocument):
    file = models.FileField(
        upload_to="wagtail_docs/", storage="public_files", verbose_name="file"
    )


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    def get_context(self, request):
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by("-first_published_at")
        context["blogpages"] = blogpages
        return context


class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)

    main_image = models.ForeignKey(
        "website.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("main_image"),
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
    ]
