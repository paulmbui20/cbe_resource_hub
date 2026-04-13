from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up

try:
    from axes.signals import user_locked_out
except ImportError:
    user_locked_out = None

from resources.models import ResourceItem
from .notifier import notify_signup, notify_lockout, notify_resource_upload

import logging

logger = logging.getLogger(__name__)


@receiver(user_signed_up)
def handle_user_signed_up(sender, request, user, **kwargs):
    """Triggers admin notification on new user signup."""
    logger.info(f"Signal received: user_signed_up for {user.email}")
    notify_signup(user)


if user_locked_out:
    @receiver([user_locked_out])
    def handle_axes_security_event(sender, request, username, ip_address, **kwargs):
        """Triggers admin notification on IP lockout or repeated access denial."""
        logger.warning(f"Security signal received: {ip_address} | {username}")
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        notify_lockout(ip_address, username, user_agent)


@receiver(post_save, sender=ResourceItem)
def handle_resource_post_save(sender, instance, created, **kwargs):
    """Triggers admin notification on new resource upload."""
    if created:
        notify_resource_upload(instance)
