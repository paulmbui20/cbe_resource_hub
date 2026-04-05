"""resources/admin.py"""

from django.contrib import admin

from .models import EducationLevel, Grade, LearningArea, ResourceItem


@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 2
    fields = ("name", "order")
    ordering = ("order",)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "order")
    list_filter = ("level",)
    ordering = ("level__order", "order", "name")


@admin.register(LearningArea)
class LearningAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(ResourceItem)
class ResourceItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "grade",
        "learning_area",
        "is_free",
        "price",
        "downloads",
        "vendor",
        "created_at",
    )
    list_filter = ("is_free", "grade__level", "learning_area")
    search_fields = ("title", "description", "vendor__username")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("downloads", "created_at", "updated_at")
    raw_id_fields = ("vendor",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Content",
            {"fields": ("title", "slug", "description", "file")},
        ),
        (
            "Curriculum",
            {"fields": ("grade", "learning_area")},
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
