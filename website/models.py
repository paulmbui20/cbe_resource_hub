"""
website/models.py

Stores submitted contact form messages so admins can read and manage
them from the custom management panel.
"""
from __future__ import annotations

from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class ContactMessage(models.Model):
    """A message submitted via the public Contact Us form."""

    name = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    phone = PhoneNumberField(
        blank=True,
        null=True,
        default=None,
        help_text="Optional phone number provided by the sender.",
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark as read after the admin has reviewed this message.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self) -> str:
        status = "✓" if self.is_read else "●"
        return f"[{status}] {self.name} — {self.subject}"
