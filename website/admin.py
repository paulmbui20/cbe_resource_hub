from django.contrib import admin
from .models import ContactMessage, Partner


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'message', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'link', 'created_at', 'slug')
    search_fields = ('name', 'link')
    list_filter = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
