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
