from django.contrib import admin
from django.utils.html import format_html

from seo.models import SlugRedirect


class SEOAdminMixin:
    """
    Enhanced mixin for ModelAdmin classes to display SEO fields with character counters.
    """

    def get_seo_fieldset(self):
        return (
            'SEO Settings', {
            'classes': ('collapse',),
            'fields': (
                'featured_image',
                'focus_keyword',
                'meta_title',
                'meta_description',
                'meta_keywords',
                'seo_preview'
            ),
            'description': 'Optimize your page for search engines. Leave fields blank for auto-generated defaults.'
        }
        )

    def seo_preview(self, obj):
        """Display a preview of how the page will appear in search results"""
        if not obj.pk:
            return "Save the object first to see SEO preview"

        title = obj.get_meta_title() if hasattr(obj, 'get_meta_title') else str(obj)
        description = obj.get_meta_description() if hasattr(obj, 'get_meta_description') else ''

        # Truncate for display
        title_display = title[:60] + '...' if len(title) > 60 else title
        desc_display = description[:160] + '...' if len(description) > 160 else description

        html = f"""
        <div style="max-width: 600px; font-family: Arial, sans-serif;">
            <div style="margin-bottom: 10px;">
                <strong>Search Preview:</strong>
            </div>
            <div id="seo-preview-box" style="border: 1px solid #ddd; padding: 12px; border-radius: 4px; background: #fff;">
                <div id="seo-preview-title" style="color: #1a0dab; font-size: 18px; margin-bottom: 4px;">
                    {title_display}
                </div>
                <div id="seo-preview-url" style="color: #006621; font-size: 14px; margin-bottom: 4px;">
                    example.com › page-url
                </div>
                <div id="seo-preview-description" style="color: #545454; font-size: 13px; line-height: 1.4;">
                    {desc_display}
                </div>
            </div>
            <div id="seo-preview-counters" style="margin-top: 8px; font-size: 12px; color: #666;">
                <span id="seo-title-count" style="color: {'red' if len(title) > 60 else 'green'}">
                    Title: {len(title)}/60 chars
                </span>
                &nbsp;|&nbsp;
                <span id="seo-desc-count" style="color: {'red' if len(description) > 160 else 'green'}">
                    Description: {len(description)}/160 chars
                </span>
            </div>
        </div>
        """

        return format_html(html, title_display, desc_display)

    seo_preview.short_description = "Search Engine Preview"

    readonly_fields = ('seo_preview',)

    class Media:
        css = {
            'all': ('admin/css/seo-admin.css',)
        }
        js = ('admin/js/seo-counter.js',)


@admin.register(SlugRedirect)
class SlugRedirectAdmin(admin.ModelAdmin):
    """Admin interface for managing slug redirects"""

    list_display = [
        'old_slug',
        'new_slug',
        'content_type',
        'object_id',
        'hit_count',
        'created_at',
    ]

    list_filter = [
        'content_type',
        'created_at',
    ]

    search_fields = [
        'old_slug',
        'new_slug',
    ]

    readonly_fields = [
        'content_type',
        'object_id',
        'created_at',
        'hit_count',
    ]

    ordering = ['-created_at']

    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        """Redirects are created automatically, prevent manual creation"""
        return False

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('content_type')
