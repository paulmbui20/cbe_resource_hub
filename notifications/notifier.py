import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Notification
from .tasks import send_notification_task

logger = logging.getLogger(__name__)

from django.db import transaction


def _get_admins():
    admins = [email for name, email in settings.ADMINS]
    logger.info(admins)
    if admins:
        return admins
    else:
        return []


def _send_template_email(recipient, subject, template_name, context, notification_type, idempotency_key=None):
    """
    Internal helper to create a Notification record and queue the Celery task.
    """
    if idempotency_key and Notification.objects.filter(idempotency_key=idempotency_key).exists():
        logger.info(f"Notification with idempotency key {idempotency_key} already exists. Skipping.")
        return None

    # Inject current year into context
    context['current_year'] = timezone.now().year

    content_html = render_to_string(f"notifications/{template_name}.html", context)
    content_text = render_to_string(f"notifications/{template_name}.txt", context)

    notification = Notification.objects.create(
        notification_type=notification_type,
        recipient_email=recipient,
        subject=subject,
        content_html=content_html,
        content_text=content_text,
        idempotency_key=idempotency_key,
        metadata=context.get('metadata', {})
    )

    # Queue for asynchronous delivery only after database commit
    transaction.on_commit(lambda: send_notification_task.delay(notification.id))
    return notification


def notify_signup(user):
    """Notifies admins of a new user signup."""

    subject = f"New User Signup: {user.email}"
    context = {'user': user}

    # Send to the first admin (or loop for all, but for simplicity let's stick to DEFAULT_FROM_EMAIL or ADMINS[0])
    for admin_email in _get_admins():
        _send_template_email(
            recipient=admin_email,
            subject=subject,
            template_name='signup_admin',
            context=context,
            notification_type=Notification.Type.SIGNUP,
            idempotency_key=f"signup_{user.id}_{admin_email}"
        )


def notify_contact_form(contact_message):
    """Notifies admins of a new contact form message."""

    subject = f"Contact Message: {contact_message.subject}"
    context = {'message': contact_message}

    for admin_email in _get_admins():
        _send_template_email(
            recipient=admin_email,
            subject=subject,
            template_name='contact_form',
            context=context,
            notification_type=Notification.Type.CONTACT,
            idempotency_key=f"contact_{contact_message.id}_{admin_email}"
        )


def notify_lockout(ip_address, username, user_agent):
    """Notifies admins of a brute-force burnout / IP lockout."""

    subject = f"Security Alert: IP Lockout detected ({ip_address})"
    context = {
        'ip_address': ip_address,
        'username': username,
        'user_agent': user_agent,
        'timestamp': timezone.now()
    }

    for admin_email in _get_admins():
        _send_template_email(
            recipient=admin_email,
            subject=subject,
            template_name='security_alert',
            context=context,
            notification_type=Notification.Type.SECURITY_ALERT,
            idempotency_key=f"lockout_{ip_address}_{timezone.now().strftime('%Y%m%d%H')}_{admin_email}"
            # 1 lockout per hour per admin
        )


def notify_resource_upload(resource):
    """Notifies admins of a new resource upload."""

    subject = f"New Resource Upload: {resource.title}"
    context = {'resource': resource}

    for admin_email in _get_admins():
        _send_template_email(
            recipient=admin_email,
            subject=subject,
            template_name='resource_upload',
            context=context,
            notification_type=Notification.Type.RESOURCE_UPLOAD,
            idempotency_key=f"resource_{resource.id}_{admin_email}"
        )


def notify_generic_message(subject, message, context):
    """Notifies admins of a new message.
    it takes params of subject, message, context
    subject is the subject of the email,
    message is the body content of the email,
    and context is the context/special info of the email
    """
    context = {
        'context': context,
        'message': message,
        'subject': subject,
    }
    for admin_email in _get_admins():
        _send_template_email(
            recipient=admin_email,
            subject=subject,
            context={'context': context},
            notification_type=Notification.Type.GENERIC_MESSAGE,
            idempotency_key=f"generic_message_{context}_{admin_email}",
            template_name='generic_message'
        )
