"""
accounts/adapters.py

Custom django-allauth adapters for the CBE Resource Hub.

AccountAdapter
  • Email-only sign-up (no username field shown to users).
  • Auto-generates an internal username from the email local-part.
  • Prevents duplicate usernames by appending a numeric suffix.

SocialAccountAdapter
  • Connects Google OAuth accounts to existing email accounts automatically.
  • Populates first_name / last_name from the Google profile.
"""
from __future__ import annotations

import unicodedata
from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.http import HttpRequest

User = get_user_model()


def _slugify_username(email: str) -> str:
    """
    Derive a safe ASCII username from the email local-part.

    Example: "Jane.Doe+tag@example.com" → "janedoe"
    """
    local = email.split("@")[0]
    # Normalize unicode, strip non-ascii, lowercase, keep alphanum
    normalized = unicodedata.normalize("NFKD", local).encode("ascii", "ignore").decode()
    slug = "".join(c for c in normalized.lower() if c.isalnum())
    return slug or "user"


def _unique_username(base: str) -> str:
    """Ensure `base` is unique; append a counter suffix if it already exists."""
    candidate = base[:148]  # leave room for the suffix
    if not User.objects.filter(username=candidate).exists():
        return candidate
    counter = 1
    while User.objects.filter(username=f"{candidate}{counter}").exists():
        counter += 1
    return f"{candidate}{counter}"


class AccountAdapter(DefaultAccountAdapter):
    """
    Email-first account adapter.

    - populate_username: auto-generates from email (users never see the field).
    - save_user: stores first_name / last_name when provided.
    """

    def populate_username(self, request: HttpRequest, user: Any) -> None:  # type: ignore[override]
        """Auto-populate username from email — no user input needed."""
        base = _slugify_username(user.email)
        user.username = _unique_username(base)

    def save_user(self, request: HttpRequest, user: Any, form: Any, commit: bool = True) -> Any:  # type: ignore[override]
        user = super().save_user(request, user, form, commit=False)
        # Ensure username is always set (in case populate_username wasn't called)
        if not user.username:
            base = _slugify_username(user.email)
            user.username = _unique_username(base)
        if commit:
            user.save()
        return user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Social account adapter.

    - pre_social_login: auto-connects Google accounts to existing users
      with matching verified emails (avoids duplicate account creation).
    - populate_user: copies first_name / last_name from the social profile.
    """

    def pre_social_login(self, request: HttpRequest, sociallogin: Any) -> None:
        """
        Transparently connect an OAuth login to an existing local account when
        the social provider email matches a verified local email.
        """
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get("email", "").lower().strip()
        if not email:
            return

        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        # Connect the social account and log the user in
        sociallogin.connect(request, existing_user)

    def populate_user(
        self, request: HttpRequest, sociallogin: Any, data: dict[str, Any]
    ) -> Any:
        user = super().populate_user(request, sociallogin, data)

        # Copy name fields from Google profile if available
        if not user.first_name:
            user.first_name = data.get("first_name", "")
        if not user.last_name:
            user.last_name = data.get("last_name", "")

        # Always generate a valid username
        if not user.username and user.email:
            base = _slugify_username(user.email)
            user.username = _unique_username(base)

        return user
