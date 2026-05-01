"""cms/admin.py"""

from django.contrib import admin

from seo.admin import SEOAdminMixin
from .models import Menu, MenuItem, Page, SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value_preview")
    search_fields = ("key", "value")
    ordering = ("key",)

    @admin.display(description="Value (preview)")
    def value_preview(self, obj: SiteSetting) -> str:
        return obj.value[:80] + "…" if len(obj.value) > 80 else obj.value


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ("title", "url", "parent", "order")
    ordering = ("order",)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("title", "menu", "parent", "url", "order")
    list_filter = ("menu",)
    search_fields = ("title", "url")
    ordering = ("menu", "order")


@admin.register(Page)
class PageAdmin(SEOAdminMixin, admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "focus_keyword", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "content", "meta_title", "focus_keyword")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Page", {"fields": ("title", "slug", "content", "is_published")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
