from website.models import FAQ
from website.models import Testimonial
from django.contrib import admin

from seo.admin import SEOAdminMixin
from .models import ContactMessage, Partner, EmailSubscriber


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "subject", "message", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "email", "phone", "subject", "message")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(Partner)
class PartnerAdmin(SEOAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "link",
        "show_as_banner",
        "created_at",
        "slug",
        "focus_keyword",
    )
    search_fields = ("name", "link", "meta_title", "focus_keyword")
    list_filter = ("show_as_banner", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            "Partner Info",
            {
                "fields": (
                    "name",
                    "slug",
                    "link",
                    "logo",
                    "description",
                    "show_as_banner",
                    "banner_cta",
                )
            },
        ),
    )


@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "opted_out", "created_at", "updated_at")
    search_fields = (
        "full_name",
        "email",
    )
    list_filter = ("opted_out", "created_at", "updated_at")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        "author_name",
        "rating",
        "body",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("rating", "is_active", "created_at", "updated_at")
    search_fields = ("author_name", "body")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "answer", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("question", "answer")


# ── Blog Comment Admin ────────────────────────────────────────────────────────
from .models import BlogComment  # noqa: E402


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ("name", "page", "short_body", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at", "page")
    search_fields = ("name", "email", "body", "page__title")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "user", "page")
    list_editable = ("is_approved",)
    actions = ["approve_comments", "reject_comments"]

    @admin.display(description="Comment")
    def short_body(self, obj):
        return obj.body[:80] + "…" if len(obj.body) > 80 else obj.body

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comment(s) approved.")

    @admin.action(description="Reject / hide selected comments")
    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} comment(s) hidden.")
