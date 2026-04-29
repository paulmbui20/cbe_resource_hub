import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from .models import Notification

logger = logging.getLogger(__name__)

@shared_task(
    bind=True, 
    max_retries=5, 
    default_retry_delay=60,
    rate_limit='10/m',
    name='notifications.send_notification'
)
def send_notification_task(self, notification_id):
    """
    Sends a notification email asynchronously.
    Updates the Notification model status and tracks retries.
    """
    try:
        notification = Notification.objects.get(pk=notification_id)
    except Notification.DoesNotExist:
        # Fail-safe: if the task runs before the DB has finished committing (highly unlikely with on_commit but possible in high-load)
        if self.request.retries < 2:
            logger.warning(f"Notification {notification_id} not found. Retrying in 2s...")
            raise self.retry(countdown=2)
        logger.error(f"Notification {notification_id} not found after 2 retries.")
        return

    if notification.status == Notification.Status.SENT:
        return f"Notification {notification_id} already sent."

    try:
        # Update status to RETRYING if it's a retry
        if self.request.retries > 0:
            notification.status = Notification.Status.RETRYING
            notification.retry_count = self.request.retries
            notification.save(update_fields=['status', 'retry_count'])

        # Prepare and send mail
        msg = EmailMultiAlternatives(
            subject=notification.subject,
            body=notification.content_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.recipient_email],
        )
        if notification.content_html:
            msg.attach_alternative(notification.content_html, "text/html")

        # In production/SMTP mode this might raise an exception
        msg.send()

        # Update success state
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at'])
        
        logger.info(f"Successfully sent notification {notification_id} to {notification.recipient_email}")
        return f"Sent to {notification.recipient_email}"

    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.last_error = str(exc)
        notification.retry_count = self.request.retries
        notification.save(update_fields=['status', 'last_error', 'retry_count'])
        
        logger.error(f"Failed to send notification {notification_id}: {str(exc)}")
        
        # Exponential backoff retry
        # (initial: 60s, then 120s, 240s, 480s, 960s)
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)
