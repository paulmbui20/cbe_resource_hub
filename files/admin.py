from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html

from .models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail",
        "title",
        "file_category",
        "mime_type",
        "human_size",
        "dimensions",
        "file_status",
        "created",
    )
    list_filter = ("file_category", "mime_type", "created")
    search_fields = ("title", "mime_type", "extension", "file_hash")

    readonly_fields = (
        "preview",
        "mime_type",
        "extension",
        "file_category",
        "size",
        "width",
        "height",
        "file_hash",
        "metadata",
        "file_url_display",
        "created",
        "updated",
    )

    fieldsets = (
        ("Basic Info", {
            "fields": ("title", "file", "preview"),
        }),
        ("Metadata", {
            "fields": (
                ("mime_type", "extension", "file_category"),
                ("size", "width", "height"),
                "file_hash",
                "metadata",
            ),
            "classes": ("collapse",),
        }),
        ("Links & Info", {
            "fields": ("file_url_display",),
        }),
        ("Timestamps", {
            "fields": ("created", "updated"),
            "classes": ("collapse",),
        }),
    )

    # Admin actions
    actions = ['check_file_existence', 'regenerate_metadata']

    # -------------------------------
    # LIST THUMBNAIL (Grid-like look)
    # -------------------------------
    def thumbnail(self, obj):
        """Display thumbnail in list view."""
        if not obj.file:
            return "—"

        try:
            if obj.file_category == "image":
                return format_html(
                    '<img src="{}" style="height:50px;width:50px;object-fit:cover;border-radius:4px;" alt="{}" />',
                    obj.url,
                    obj.title
                )
            elif obj.file_category == "video":
                return format_html(
                    '<div style="height:50px;width:50px;background:#333;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:20px;">▶</div>',
                    obj.url,
                    obj.title
                )
            elif obj.file_category == "document":
                return format_html(
                    '<div style="height:50px;width:50px;background:#e8f4f8;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:20px;">📄</div>',
                    obj.url,
                    obj.title
                )
        except Exception:
            pass

        return "—"

    thumbnail.short_description = "Preview"

    # -------------------------------
    # DETAIL PREVIEW (Larger)
    # -------------------------------
    def preview(self, obj):
        """Preview depending on file type."""
        if not obj.file:
            return "No File"

        try:
            if obj.file_category == "image":
                return format_html(
                    '''
                    <div style="margin:10px 0;">
                        <img src="{}" style="max-width:400px;max-height:400px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);" alt="{}" />
                        <p style="margin-top:10px;color:#666;font-size:12px;">
                            Dimensions: {}×{}<br>
                            Size: {}
                        </p>
                    </div>
                    ''',
                    obj.url,
                    obj.title,
                    obj.width or '?',
                    obj.height or '?',
                    obj.human_size
                )

            if obj.file_category == "video":
                return format_html(
                    '''
                    <div style="margin:10px 0;">
                        <video width="400" controls style="border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                            <source src="{}" type="{}">
                            Your browser does not support video playback.
                        </video>
                        <p style="margin-top:10px;color:#666;font-size:12px;">
                            Size: {}
                        </p>
                    </div>
                    ''',
                    obj.url,
                    obj.mime_type,
                    obj.human_size
                )

            # Documents / Others
            return format_html(
                '''
                <div style="margin:10px 0;">
                    <a href="{}" target="_blank" style="display:inline-block;padding:10px 20px;background:#0066cc;color:white;text-decoration:none;border-radius:4px;">
                        Open file in new tab
                    </a>
                    <p style="margin-top:10px;color:#666;font-size:12px;">
                        Type: {}<br>
                        Size: {}
                    </p>
                </div>
                ''',
                obj.url,
                obj.mime_type,
                obj.human_size
            )
        except Exception as e:
            return format_html('<p style="color:red;">Error loading preview: {}</p>', str(e))

    preview.short_description = "Preview"

    # -------------------------------
    # DIMENSIONS COLUMN
    # -------------------------------
    def dimensions(self, obj):
        """Show image dimensions in list view."""
        if obj.width and obj.height:
            return f"{obj.width}×{obj.height}"
        return "—"

    dimensions.short_description = "Dimensions"

    # -------------------------------
    # FILE STATUS (existence check)
    # -------------------------------
    def file_status(self, obj):
        """Check if file exists in storage."""
        try:
            if obj.file_exists():
                return format_html(
                    '<span style="color:green;">✓ Exists</span>',
                    obj,
                    obj.file_exists
                )
            else:
                return format_html(
                    '<span style="color:red;">✗ Missing</span>',
                    obj,
                    obj.file_exists
                )
        except Exception:
            return format_html(
                '<span style="color:orange;">? Unknown</span>',
                obj,
                obj.file_exists,
            )

    file_status.short_description = "Status"

    # -------------------------------
    # FILE URL DISPLAY
    # -------------------------------
    def file_url_display(self, obj):
        """Display clickable file URL."""
        if not obj.url:
            return "No URL"

        return format_html(
            '<a href="{}" target="_blank" style="word-break:break-all;">{}</a>',
            obj.url,
            obj.url
        )

    file_url_display.short_description = "File URL"

    # -------------------------------
    # ADMIN ACTIONS
    # -------------------------------
    def check_file_existence(self, request, queryset):
        """Check if selected files exist in storage."""
        missing_count = 0
        for file_obj in queryset:
            if not file_obj.file_exists():
                missing_count += 1
                self.message_user(
                    request,
                    f"Missing: {file_obj.title} (ID: {file_obj.pk})",
                    level='warning'
                )

        if missing_count == 0:
            self.message_user(request, "All selected files exist in storage.", level='success')
        else:
            self.message_user(
                request,
                f"{missing_count} file(s) are missing from storage.",
                level='error'
            )

    check_file_existence.short_description = "Check if files exist in storage"

    def regenerate_metadata(self, request, queryset):
        """Regenerate metadata for selected files."""
        success_count = 0
        error_count = 0

        for file_obj in queryset:
            try:
                file_obj._extract_metadata()
                file_obj.save()
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error regenerating metadata for {file_obj.title}: {str(e)}",
                    level='error'
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully regenerated metadata for {success_count} file(s).",
                level='success'
            )

        if error_count > 0:
            self.message_user(
                request,
                f"Failed to regenerate metadata for {error_count} file(s).",
                level='error'
            )

    regenerate_metadata.short_description = "Regenerate metadata"

    # -------------------------------
    # CHANGELIST CUSTOMIZATION
    # -------------------------------
    def changelist_view(self, request, extra_context=None):
        """Add statistics to changelist view."""
        extra_context = extra_context or {}

        # Calculate statistics
        stats = File.objects.aggregate(
            total_count=Count('id'),
            total_size=Sum('size'),
        )

        # Category breakdown
        category_stats = File.objects.values('file_category').annotate(
            count=Count('id'),
            total_size=Sum('size')
        ).order_by('-count')

        extra_context['stats'] = stats
        extra_context['category_stats'] = category_stats

        return super().changelist_view(request, extra_context)

    # -------------------------------
    # FORM CUSTOMIZATION
    # -------------------------------
    def save_model(self, request, obj, form, change):
        """Custom save with validation."""
        try:
            # Clean will be called automatically by the form
            super().save_model(request, obj, form, change)
            self.message_user(request, f"File '{obj.title}' saved successfully.", level='success')
        except Exception as e:
            self.message_user(request, f"Error saving file: {str(e)}", level='error')
            raise
