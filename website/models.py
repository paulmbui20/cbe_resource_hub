"""
website/models.py

Stores submitted contact form messages so admins can read and manage
them from the custom management panel.
"""
from __future__ import annotations

from django.db import models
from django.db.models.functions import Lower
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField
from tinymce.models import HTMLField

from resources.validators import validate_image_file_magic


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


class Partner(models.Model):
    name = models.CharField(max_length=255)
    link = models.URLField(null=True, blank=True)
    slug = models.SlugField(max_length=255, null=True, blank=True)
    featured_image = models.ImageField(
        validators=[validate_image_file_magic],
        upload_to='partners/featured_images/',
        null=True,
    )
    description = HTMLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, using=None, keep_parents=False):
        if self.featured_image:
            self.featured_image.delete(save=False)
        return super().delete(using=using, keep_parents=keep_parents)

    def save(self, *args, **kwargs):
        if not self.slug or self.slug == '':  # or self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} Partner on URL {self.link} added on {self.created_at}" if self.link else f"{self.name} Partner"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_partner_name",
                violation_error_message="Partner with this name already exists",
            ),
            models.UniqueConstraint(
                fields=['link'],
                name="unique_partner_url",
                violation_error_message="Partner with this url already exists",
                condition=models.Q(link__isnull=False)
            ),
        ]
