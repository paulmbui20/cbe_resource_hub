"""accounts/admin.py"""
from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin for the email-first CustomUser model.

    UserAdmin assumes username is the primary identifier; we override the
    key fieldsets and list_display to make email the focal point.
    """

    list_display   = (
        "email", "username", "role", "is_vendor", "is_staff", "must_change_password",
        "disable_email_notification" ,"date_joined", "last_login",
    )
    list_filter    = ("role", "is_vendor", "is_staff", "is_active", "must_change_password", "disable_email_notification")
    search_fields  = ("email", "username", "first_name", "last_name", "phone_number")
    ordering       = ("-date_joined",)

    # Redefine fieldsets so email comes first and username is clearly secondary
    fieldsets = (
        (None, {"fields": ("email", "password", "must_change_password", "disable_email_notification")}),
        (_("Personal info"), {"fields": ("username", "first_name", "last_name", "phone_number")}),
        (_("Permissions"), {
            "fields": (
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions",
            ),
        }),
        (_("Platform"), {"fields": ("role", "is_vendor")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # Add-user form: email + password only (username is auto-generated)
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
        (_("Platform"), {
            "classes": ("wide",),
            "fields": ("role", "is_vendor"),
        }),
    )
