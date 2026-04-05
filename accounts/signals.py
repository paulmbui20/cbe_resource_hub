"""
accounts/signals.py

Post-save signal handlers for CustomUser:

1. auto_set_admin_role
   When a superuser is created (is_staff=True, is_superuser=True) — whether
   via `createsuperuser`, the admin UI, or programmatically — their role is
   automatically set to Role.ADMIN.

2. ensure_superuser_email_verified
   When a superuser first logs in via email (allauth), we create a verified
   EmailAddress record so allauth never blocks them with an unverified-email
   warning, and subsequent social logins can auto-connect to their account.
"""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from allauth.account.signals import password_changed

logger = logging.getLogger(__name__)


@receiver(post_save, sender="accounts.CustomUser")
def auto_set_admin_role(sender, instance, created: bool, **kwargs) -> None:
    """
    Automatically assign Role.ADMIN to any superuser account.

    Runs silently on every save so it self-heals if someone manually
    changes a superuser's role back.
    """
    from accounts.models import CustomUser

    if instance.is_superuser and instance.role != CustomUser.Role.ADMIN:
        # Use queryset update to avoid triggering this signal again
        sender.objects.filter(pk=instance.pk).update(
            role=CustomUser.Role.ADMIN
        )
        logger.info(
            "auto_set_admin_role: set role=admin for %s",
            instance.email,
        )


@receiver(post_save, sender="accounts.CustomUser")
def ensure_superuser_email_verified(
    sender, instance, created: bool, **kwargs
) -> None:
    """
    When a superuser is saved (created or updated), ensure allauth has a
    verified EmailAddress record for their email.

    This means:
    - `createsuperuser` → verified record created immediately.
    - Admin-created superusers → verified on first save.
    - Subsequent Django allauth logins won't prompt for email confirmation.
    - Social logins (Google) will auto-connect to the same account.
    """
    if not instance.is_superuser or not instance.email:
        return

    try:
        from allauth.account.models import EmailAddress

        obj, created_record = EmailAddress.objects.get_or_create(
            user=instance,
            email__iexact=instance.email,
            defaults={
                "email": instance.email,
                "primary": True,
                "verified": True,
            },
        )

        if not created_record and not obj.verified:
            obj.verified = True
            obj.primary = True
            obj.save(update_fields=["verified", "primary"])

            logger.info(
                "ensure_superuser_email_verified: marked %s as verified",
                instance.email,
            )

    except Exception:
        # Never crash a save because of this housekeeping step
        logger.exception(
            "ensure_superuser_email_verified: failed for %s",
            instance.email,
        )


@receiver(password_changed)
def reset_must_change_password(sender, request, user, **kwargs):
    if getattr(user, "must_change_password", False):
        user.must_change_password = False
        user.save(update_fields=["must_change_password"])
        