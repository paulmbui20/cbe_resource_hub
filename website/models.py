"""
website/models.py

Stores submitted contact form messages so admins can read and manage
them from the custom management panel.
"""

from taggit.forms import TagWidget
from datetime import date

from django.db import models
from django.core.files.storage import storages
from django.db.models.functions import Lower
from django.utils.html import strip_tags
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField
from core.fields import SafeHTMLField

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.images.models import AbstractImage, AbstractRendition, Image
from wagtail.documents.models import AbstractDocument, Document

from taggit.models import TaggedItemBase
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager

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
    description = SafeHTMLField(null=True, blank=True)
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
        upload_to="wagtail_images/",
        storage=storages["public_files"],
        verbose_name="file",
        width_field="width",
        height_field="height",
        validators=[validate_image_file],
    )

    admin_form_fields = Image.admin_form_fields


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(
        CustomImage, on_delete=models.CASCADE, related_name="renditions"
    )
    file = models.ImageField(
        upload_to="wagtail_renditions/",
        storage=storages["public_files"],
        width_field="width",
        height_field="height",
        validators=[validate_image_file],
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)


class CustomDocument(AbstractDocument):
    file = models.FileField(
        upload_to="wagtail_docs/",
        storage=storages["public_files"],
        verbose_name="file",
    )

    admin_form_fields = Document.admin_form_fields


class BlogIndexPage(Page):
    """This page is the parent page for all blog pages.
    It will display all blog pages in a list.
    Only One such page can be created.
    """

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    def get_context(self, request):

        tag = request.GET.get("tag")
        if tag:
            blogpages = (
                BlogPage.objects.filter(
                    tags__name=tag,
                    live=True,
                )
                .select_related("main_image", "author", "author__image")
                .prefetch_related("tags")
                .order_by("-first_published_at")
            )
        else:
            blogpages = (
                BlogPage.objects.child_of(self)
                .live()
                .select_related("main_image", "author", "author__image")
                .prefetch_related("tags")
                .order_by("-first_published_at")
            )

        context = super().get_context(request)
        context["blogpages"] = blogpages
        return context


@register_snippet
class BlogAuthor(models.Model):
    """An author for blog posts."""

    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    image = models.ForeignKey(
        "website.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Blog Author"
        verbose_name_plural = "Blog Authors"


class BlogPage(Page):
    """A single blog post. It will be displayed in a list on the BlogIndexPage."""

    date = models.DateField("Post date", default=date.today)
    intro = models.CharField(max_length=250, blank=True, default="")
    body = RichTextField(blank=True, default="")
    views = models.PositiveIntegerField(default=0, editable=False)

    author = models.ForeignKey(
        "BlogAuthor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="blog_posts",
    )

    main_image = models.ForeignKey(
        "website.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    tags = ClusterTaggableManager(through="BlogTag", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("author"),
        FieldPanel("date"),
        FieldPanel("main_image"),
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("tags", widget=TagWidget),
    ]

    def serve(self, request):
        # Efficiently increment view count
        BlogPage.objects.filter(pk=self.pk).update(views=models.F("views") + 1)
        return super().serve(request)

    def get_context(self, request):
        context = super().get_context(request)
        
        # Re-fetch the page with optimizations to avoid N+1 in templates
        # We use .get() to ensure we have the prefetched data on the object
        optimized_page = BlogPage.objects.filter(pk=self.pk).select_related(
            "author", "author__image", "main_image"
        ).prefetch_related("tags").first()

        if optimized_page:
            context["page"] = optimized_page
            # Cache tags and parent to avoid repeated queries in template
            context["tags"] = optimized_page.tags.all()
            context["parent"] = optimized_page.get_parent()
            
            # Pre-calculate siblings
            context["prev_post"] = optimized_page.get_prev_sibling()
            context["next_post"] = optimized_page.get_next_sibling()
        
        return context


class BlogTag(TaggedItemBase):
    content_object = ParentalKey(
        "website.BlogPage", on_delete=models.CASCADE, related_name="tagged_items"
    )


# ──────────────────────────────────────────────────────────────────────────────
# SOCIAL PROOF (TESTIMONIALS) AND FAQs MODELS
# ──────────────────────────────────────────────────────────────────────────────


class Testimonial(TimeStampedModel, models.Model):
    """Social proof testimonial with optional star rating."""

    __test__ = False  # Prevent pytest from collecting this as a test class

    STARS = [(i, f"{i} star{'s' if i != 1 else ''}") for i in range(1, 6)]

    author_name = models.CharField(max_length=150)
    author_role = models.CharField(max_length=200, blank=True, default="")
    author_organization = models.CharField(max_length=200, blank=True, default="")
    author_avatar = models.ImageField(
        upload_to="testimonials/avatars/",
        blank=True,
        help_text="Optional profile photo for the author.",
        validators=[validate_image_file],
        null=True,
    )
    body = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=STARS, default=5)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "order"]
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return f"{self.author_name} — {self.rating}★"


class FAQ(TimeStampedModel, models.Model):
    """Frequently asked question."""

    question = models.CharField(max_length=500)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "order"]
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question[:80]
