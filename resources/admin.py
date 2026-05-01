"""resources/admin.py"""

from django.contrib import admin

from seo.admin import SEOAdminMixin
from .models import EducationLevel, Grade, LearningArea, ResourceItem


@admin.register(EducationLevel)
class EducationLevelAdmin(SEOAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 2
    fields = ("name", "order", "slug")
    ordering = ("order",)


@admin.register(Grade)
class GradeAdmin(SEOAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "level", "order")
    list_filter = ("level",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(LearningArea)
class LearningAreaAdmin(SEOAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(ResourceItem)
class ResourceItemAdmin(SEOAdminMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "grade",
        "learning_area",
        "resource_type",
        "is_free",
        "price",
        "downloads",
        "vendor",
        "created_at",
    )
    list_filter = ("is_free", "grade__level", "learning_area", "resource_type")
    search_fields = ("title", "description", "vendor__username")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("downloads", "created_at", "updated_at")
    raw_id_fields = ("vendor",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Content",
            {"fields": ("title", "slug", "resource_type", "description", "file")},
        ),
        (
            "Curriculum",
            {"fields": ("grade", "learning_area", "academic_session")},
        ),
        (
            "Marketplace",
            {"fields": ("vendor", "is_free", "price", "downloads")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
