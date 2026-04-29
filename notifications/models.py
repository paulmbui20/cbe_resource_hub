from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class Notification(models.Model):
    """
    Tracks outgoing system notifications and their delivery status.
    All system emails should be logged here first and then processed by Celery.
    """

    class Type(models.TextChoices):
        SIGNUP = 'SIGNUP', _('User Signup')
        CONTACT = 'CONTACT', _('Contact Form Submission')
        RESOURCE_UPLOAD = 'RESOURCE_UPLOAD', _('Resource Upload')
        SECURITY_ALERT = 'SECURITY_ALERT', _('Security Alert (Lockout)')
        GENERAL = 'GENERAL', _('General')
        GENERIC_MESSAGE = 'GENERIC_MESSAGE', _('Generic Message')

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SENT = 'SENT', _('Sent')
        FAILED = 'FAILED', _('Failed')
        RETRYING = 'RETRYING', _('Retrying')

    notification_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.GENERAL,
        db_index=True
    )
    recipient_email = models.EmailField(_('recipient email address'))
    subject = models.CharField(max_length=255)
    content_html = models.TextField(blank=True)
    content_text = models.TextField(blank=True)
    
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, null=True)
    
    # Prevents duplicate notifications for the same event
    idempotency_key = models.CharField(
        max_length=255, 
        unique=True, 
        blank=True, 
        null=True,
        db_index=True
    )
    
    # Store arbitrary data related to the event (e.g., user_id, resource_id)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.notification_type} to {self.recipient_email}"
