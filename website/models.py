"""
website/models.py

Stores submitted contact form messages so admins can read and manage
them from the custom management panel.
"""

from taggit.forms import TagWidget
from datetime import date

from django.db import models
from django.db.models import Count, Q
import math
from django import forms
from django.core.files.storage import storages
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField
from core.fields import SafeHTMLField

from wagtail import blocks
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.table_block.blocks import TableBlock

from wagtail.snippets.models import register_snippet
from wagtail.images.models import AbstractImage, AbstractRendition
from wagtail.documents.models import AbstractDocument
from wagtail.contrib.routable_page.models import RoutablePageMixin, route

from taggit.models import TaggedItemBase
from modelcluster.fields import ParentalKey, ParentalManyToManyField
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


def get_public_storage():
    """Callable to return the public storage backend, preventing migration flapping
    when environments (like CI/CD vs Prod) have different storage configs."""
    return storages["public_files"]


class CustomImage(AbstractImage):
    file = models.ImageField(
        upload_to="wagtail_images/",
        storage=get_public_storage,
        verbose_name="file",
        width_field="width",
        height_field="height",
        validators=[validate_image_file],
    )

    admin_form_fields = (
        "title",
        "file",
        "collection",
        "tags",
        "focal_point_x",
        "focal_point_y",
        "focal_point_width",
        "focal_point_height",
    )


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(
        CustomImage, on_delete=models.CASCADE, related_name="renditions"
    )
    file = models.ImageField(
        upload_to="wagtail_renditions/",
        storage=get_public_storage,
        width_field="width",
        height_field="height",
        validators=[validate_image_file],
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)


class CustomDocument(AbstractDocument):
    file = models.FileField(
        upload_to="wagtail_docs/",
        storage=get_public_storage,
        verbose_name="file",
    )

    admin_form_fields = (
        "title",
        "file",
        "collection",
        "tags",
    )


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    icon = models.ForeignKey(
        "website.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("icon"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Blog Categories"


class BlogIndexPage(RoutablePageMixin, Page):
    """This page is the parent page for all blog pages.
    It will display all blog pages in a list.
    Only One such page can be created.
    """

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    def get_blogpages(self):
        return (
            BlogPage.objects.child_of(self)
            .live()
            .select_related("main_image", "author", "author__image")
            .prefetch_related("tags", "categories")
            .annotate(
                approved_comments_count=Count(
                    "comments", filter=Q(comments__is_approved=True)
                )
            )
            .order_by("-first_published_at")
        )

    def get_context(self, request):
        context = super().get_context(request)
        context["blogpages"] = self.get_blogpages()
        context["index_url"] = self.url
        return context

    @route(r"^category/(?P<category_slug>[-\w]+)/$")
    def category_filter(self, request, category_slug):
        category = BlogCategory.objects.get(slug=category_slug)
        blogpages = self.get_blogpages().filter(categories__slug=category_slug)
        return self.render(
            request,
            context_overrides={
                "blogpages": blogpages,
                "filter_type": "Category",
                "filter_term": category.name,
            },
        )

    @route(r"^author/(?P<author_slug>[-\w]+)/$")
    def author_filter(self, request, author_slug):
        author = BlogAuthor.objects.get(slug=author_slug)
        blogpages = self.get_blogpages().filter(author__slug=author_slug)
        return self.render(
            request,
            context_overrides={
                "blogpages": blogpages,
                "filter_type": "Author",
                "filter_term": author.name,
                "author": author,
            },
        )

    @route(r"^tag/(?P<tag_slug>[-\w]+)/$")
    def tag_filter(self, request, tag_slug):
        blogpages = self.get_blogpages().filter(tags__slug=tag_slug)
        return self.render(
            request,
            context_overrides={
                "blogpages": blogpages,
                "filter_type": "Tag",
                "filter_term": tag_slug,
            },
        )


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
    instagram = models.URLField(blank=True)

    tiktok = models.URLField(blank=True)

    twitter = models.URLField(blank=True)

    youtube = models.URLField(blank=True)

    linkedin = models.URLField(blank=True)

    whatsapp = models.URLField(blank=True)

    telegram = models.URLField(blank=True)

    email = models.EmailField(blank=True)

    website = models.URLField(blank=True)
    slug = models.SlugField(unique=True, max_length=255, blank=True, null=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("role"),
        FieldPanel("bio"),
        FieldPanel("image"),
        FieldPanel("facebook"),
        FieldPanel("instagram"),
        FieldPanel("tiktok"),
        FieldPanel("twitter"),
        FieldPanel("youtube"),
        FieldPanel("linkedin"),
        FieldPanel("whatsapp"),
        FieldPanel("telegram"),
        FieldPanel("email"),
        FieldPanel("website"),
    ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def post_count(self):
        return self.blog_posts.live().count()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Blog Author"
        verbose_name_plural = "Blog Authors"


class BlogPage(Page):
    """A single blog post. It will be displayed in a list on the BlogIndexPage."""

    date = models.DateField("Post date", default=date.today)
    intro = models.CharField(max_length=250, blank=True, default="")
    body = StreamField(
        [
            (
                "paragraph",
                blocks.RichTextBlock(
                    features=[
                        "h1",
                        "h2",
                        "h3",
                        "h4",
                        "h5",
                        "h6",
                        "bold",
                        "italic",
                        "blockquote",
                        "ol",
                        "ul",
                        "hr",
                        "link",
                        "image",
                        "embed",
                    ]
                ),
            ),
            ("table", TableBlock()),
        ],
        use_json_field=True,
        blank=True,
        null=True,
    )
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
    main_image_alt = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alt text for the main image (SEO optimization).",
    )
    categories = ParentalManyToManyField("website.BlogCategory", blank=True)
    tags = ClusterTaggableManager(through="BlogTag", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("author"),
        FieldPanel("date"),
        FieldPanel("main_image"),
        FieldPanel("main_image_alt"),
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("categories", widget=forms.CheckboxSelectMultiple),
        FieldPanel("tags", widget=TagWidget),
        InlinePanel("faqs", label="FAQs"),
    ]

    @property
    def reading_time(self):
        """Calculates estimated reading time in minutes."""
        # Convert StreamField to string (HTML) then strip tags
        content = strip_tags(str(self.body))
        word_count = len(content.split())
        return max(1, math.ceil(word_count / 200))

    def serve(self, request):
        # Efficiently increment view count
        BlogPage.objects.filter(pk=self.pk).update(views=models.F("views") + 1)
        return super().serve(request)

    def get_context(self, request):
        context = super().get_context(request)

        # Re-fetch the page with optimizations to avoid N+1 in templates
        # We use .get() to ensure we have the prefetched data on the object
        optimized_page = (
            BlogPage.objects.filter(pk=self.pk)
            .select_related("author", "author__image", "main_image")
            .prefetch_related("tags")
            .first()
        )

        if optimized_page:
            context["page"] = optimized_page
            # Cache tags and parent to avoid repeated queries in template
            context["tags"] = optimized_page.tags.all()
            context["parent"] = optimized_page.get_parent()

            # Pre-calculate siblings
            context["prev_post"] = optimized_page.get_prev_sibling()
            context["next_post"] = optimized_page.get_next_sibling()

            # Related articles (same category)
            category_ids = list(optimized_page.categories.values_list("id", flat=True))
            first_category = optimized_page.categories.first() if category_ids else None
            context["related_category"] = first_category

            if category_ids:
                context["related_posts"] = (
                    BlogPage.objects.live()
                    .filter(categories__id__in=category_ids)
                    .exclude(id=optimized_page.id)
                    .distinct()
                    .select_related("main_image", "author", "author__image")
                    .prefetch_related("categories", "tags")
                    .annotate(
                        approved_comments_count=Count(
                            "comments", filter=Q(comments__is_approved=True)
                        )
                    )[:3]
                )
            else:
                context["related_posts"] = (
                    BlogPage.objects.live()
                    .exclude(id=optimized_page.id)
                    .order_by("-first_published_at")
                    .select_related("main_image", "author", "author__image")
                    .prefetch_related("categories", "tags")
                    .annotate(
                        approved_comments_count=Count(
                            "comments", filter=Q(comments__is_approved=True)
                        )
                    )[:3]
                )

            # ── Comments ──────────────────────────────────────────────────
            from website.forms import BlogCommentForm  # local to avoid circular

            context["comments"] = (
                optimized_page.comments.filter(is_approved=True, parent=None)
                .select_related("user")
                .prefetch_related("replies__user")
            )
            context["comment_count"] = optimized_page.comments.filter(
                is_approved=True
            ).count()
            context["submit_url"] = reverse(
                "blog_comment_post", kwargs={"page_id": optimized_page.pk}
            )

            is_auth = request.user.is_authenticated
            context["is_auth"] = is_auth
            context["commenter_name"] = (
                (request.user.get_full_name() or request.user.username)
                if is_auth
                else ""
            )
            context["commenter_email"] = request.user.email if is_auth else ""
            context["comment_form"] = BlogCommentForm()

        return context


class BlogPageFAQ(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=255)
    answer = RichTextField()

    panels = [
        FieldPanel("question"),
        FieldPanel("answer"),
    ]


class BlogTag(TaggedItemBase):
    content_object = ParentalKey(
        "website.BlogPage", on_delete=models.CASCADE, related_name="tagged_items"
    )


# ──────────────────────────────────────────────────────────────────────────────
# BLOG COMMENTS
# ──────────────────────────────────────────────────────────────────────────────


class BlogComment(TimeStampedModel, models.Model):
    """
    A comment on a BlogPage.  Supports both authenticated users (name/email
    filled automatically) and anonymous visitors.  Designed for reuse: swap
    the ForeignKey for a GenericForeignKey when extending to resources.
    """

    page = models.ForeignKey(
        "website.BlogPage",
        on_delete=models.CASCADE,
        related_name="comments",
    )

    # ── Commenter identity ────────────────────────────────────────────────
    user = models.ForeignKey(
        "accounts.CustomUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="blog_comments",
        help_text="Set when the commenter is logged in.",
    )
    # For anonymous commenters (also pre-filled for authenticated ones).
    name = models.CharField(max_length=100)
    email = models.EmailField(
        blank=True,
        default="",
        help_text="Not displayed publicly.",
    )

    # ── Content ───────────────────────────────────────────────────────────
    body = models.TextField(max_length=2000)

    # ── Threading ─────────────────────────────────────────────────────────
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        help_text="Set to make this a reply to another comment.",
    )

    # ── Moderation ────────────────────────────────────────────────────────
    is_approved = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Uncheck to hide this comment from the public.",
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Blog Comment"
        verbose_name_plural = "Blog Comments"

    def __str__(self) -> str:
        return f'{self.name} on "{self.page.title[:40]}" at {self.created_at:%Y-%m-%d}'


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
