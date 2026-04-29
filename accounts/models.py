"""
accounts/models.py

Custom user model extending Django's AbstractUser.

Email is the primary identifier (USERNAME_FIELD = "email").
The username field is retained for compatibility but auto-generated
by the AccountAdapter; users never type a username.

Future-proofed for the multivendor marketplace with is_vendor flag and role.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class EmailUserManager(UserManager):
    """
    Custom manager that removes the `username` requirement from management
    commands (createsuperuser) and programmatic user creation.

    Users always set an email; username is auto-derived internally.
    """

    def _create_user(self, email: str, password: str | None, **extra_fields):  # type: ignore[override]
        if not email:
            raise ValueError("An email address must be provided.")
        email = self.normalize_email(email)
        # Auto-generate username from email if not provided
        if not extra_fields.get("username"):
            from accounts.adapters import _slugify_username, _unique_username
            extra_fields["username"] = _unique_username(_slugify_username(email))
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):  # type: ignore[override]
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):  # type: ignore[override]
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"]:
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields["is_superuser"]:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Extended user model for cbe_resource_hub.

    PRIMARY LOGIN:  email  (username is internal / auto-generated)
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        VENDOR = "vendor", "Vendor/Creator"
        USER = "user", "Standard User"

    objects = EmailUserManager()  # type: ignore[assignment]

    # ── Make email the unique primary identifier ──────────────────────────────
    email = models.EmailField(
        unique=True,
        help_text="Required. Used as the primary login credential.",
    )

    # username stays on the model (AbstractUser requires it) but is hidden from
    # users — auto-generated from email by the AccountAdapter / EmailUserManager.
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        help_text="Auto-generated from email. Not required at sign-up.",
    )

    # ── Marketplace / platform fields ─────────────────────────────────────────
    is_vendor: bool = models.BooleanField(
        default=False,
        help_text="Designates whether this user is a content vendor/creator.",
    )
    phone_number = PhoneNumberField(
        blank=True,
        null=True,
        help_text="Optional contact phone number.",
    )
    role: str = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
        help_text="Primary role of this user within the platform.",
    )
    must_change_password: bool = models.BooleanField(
        default=False,
        help_text="If True, the user is forced to change their password on the next login.",
    )
    disable_email_notification: bool = models.BooleanField(
        default=False,
        help_text="If checked, you will not receive marketing emails, however transactional emails will still be sent.",
    )

    # ── User Preferences ──────────────────────────────────────────────────────
    favorites = models.ManyToManyField(
        "resources.ResourceItem",
        related_name="favorited_by",
        blank=True,
    )

    # Email is the login field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # removes all extra prompts from `createsuperuser`

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.get_full_name() or self.email

    def save(self, *args, **kwargs):
        
        if self.role == CustomUser.Role.VENDOR and not self.is_vendor:
            self.is_vendor = True
        if self.is_vendor and not self.role == CustomUser.Role.VENDOR:
            self.role = CustomUser.Role.VENDOR
        if self.is_superuser and self.role != CustomUser.Role.ADMIN:
            self.role = CustomUser.Role.ADMIN

        super().save(*args, **kwargs)

    @property
    def is_content_vendor(self) -> bool:
        """True if the user is flagged as a vendor or has the vendor role."""
        return self.is_vendor or self.role == self.Role.VENDOR or \
            self.is_superuser or self.role == self.Role.ADMIN
