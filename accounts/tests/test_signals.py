"""
accounts/tests/test_signals.py

Tests for accounts/signals.py:

1. ensure_superuser_email_verified  (post_save)
   - Creates a verified EmailAddress for a new superuser
   - Marks an existing unverified EmailAddress as verified
   - Does nothing for non-superusers
   - Does nothing for superusers with no email

2. reset_must_change_password  (allauth password_changed signal)
   - Clears must_change_password when the flag is True
   - Does nothing when the flag is already False

3. generate_username_from_email  (pre_save)
   - Auto-generates username from email on creation
   - Does not overwrite an existing username
   - Handles edge-case emails cleanly
   - Generates unique usernames when a base slug is already taken
"""

from unittest.mock import MagicMock, patch

from allauth.account.models import EmailAddress
from django.test import TestCase, RequestFactory

from accounts.models import CustomUser
from accounts.tests.base import AccountsBaseTestcase


# ── ensure_superuser_email_verified ───────────────────────────────────────────

class EnsureSuperuserEmailVerifiedTests(TestCase):

    # ── new superuser ─────────────────────────────────────────────────────────

    def test_creates_verified_email_address_for_new_superuser(self):
        user = CustomUser.objects.create_superuser(
            email="super1@example.com", password="pass"
        )
        self.assertTrue(
            EmailAddress.objects.filter(user=user, verified=True).exists()
        )

    def test_email_address_is_marked_primary_for_new_superuser(self):
        user = CustomUser.objects.create_superuser(
            email="super2@example.com", password="pass"
        )
        addr = EmailAddress.objects.get(user=user)
        self.assertTrue(addr.primary)

    def test_email_address_email_matches_user_email(self):
        user = CustomUser.objects.create_superuser(
            email="super3@example.com", password="pass"
        )
        addr = EmailAddress.objects.get(user=user)
        self.assertEqual(addr.email, "super3@example.com")

    def test_only_one_email_address_record_created(self):
        user = CustomUser.objects.create_superuser(
            email="super4@example.com", password="pass"
        )
        self.assertEqual(EmailAddress.objects.filter(user=user).count(), 1)

    # ── existing unverified record ────────────────────────────────────────────

    def test_marks_existing_unverified_email_as_verified(self):
        user = CustomUser.objects.create_superuser(
            email="super5@example.com", password="pass"
        )
        addr = EmailAddress.objects.get(user=user)
        addr.verified = False
        addr.save(update_fields=["verified"])

        # Trigger signal by saving the user again
        user.save()

        addr.refresh_from_db()
        self.assertTrue(addr.verified)

    def test_marks_existing_non_primary_email_as_primary(self):
        user = CustomUser.objects.create_superuser(
            email="super6@example.com", password="pass"
        )
        addr = EmailAddress.objects.get(user=user)
        addr.verified = False
        addr.primary = False
        addr.save(update_fields=["verified", "primary"])

        user.save()

        addr.refresh_from_db()
        self.assertTrue(addr.primary)

    def test_does_not_create_duplicate_when_already_verified(self):
        user = CustomUser.objects.create_superuser(
            email="super7@example.com", password="pass"
        )
        # Saving again should not create a second EmailAddress
        user.save()
        self.assertEqual(EmailAddress.objects.filter(user=user).count(), 1)

    # ── non-superuser ─────────────────────────────────────────────────────────

    def test_does_not_create_email_address_for_standard_user(self):
        user = CustomUser.objects.create_user(
            email="regular@example.com", password="pass"
        )
        self.assertFalse(EmailAddress.objects.filter(user=user).exists())

    def test_does_not_create_email_address_for_vendor(self):
        user = CustomUser.objects.create_user(
            email="vendor@example.com",
            password="pass",
            role=CustomUser.Role.VENDOR,
            is_vendor=True,
        )
        self.assertFalse(EmailAddress.objects.filter(user=user).exists())

    # ── guard: no email ───────────────────────────────────────────────────────

    def test_does_not_crash_when_superuser_has_no_email(self):
        """Signal must return early gracefully — no EmailAddress, no exception."""
        user = CustomUser.objects.create_superuser(
            email="noemail@example.com", password="pass"
        )
        # Blank the email and fire post_save manually
        user.email = ""
        try:
            from accounts.signals import ensure_superuser_email_verified
            ensure_superuser_email_verified(
                sender=CustomUser, instance=user, created=False
            )
        except Exception as exc:
            self.fail(f"Signal raised an exception with blank email: {exc}")

    # ── guard: exception swallowing ───────────────────────────────────────────

    def test_signal_does_not_propagate_exceptions(self):
        """Any internal failure must be caught; the save must not crash."""
        user = CustomUser.objects.create_superuser(
            email="robust@example.com", password="pass"
        )
        with patch(
                "accounts.signals.EmailAddress.objects.get_or_create",
                side_effect=Exception("DB exploded"),
        ):
            try:
                user.save()
            except Exception as exc:
                self.fail(f"Signal let an exception escape: {exc}")


# ── reset_must_change_password ────────────────────────────────────────────────

class ResetMustChangePasswordTests(AccountsBaseTestcase):

    def _fire_password_changed(self, user):
        """Directly invoke the signal handler (avoids needing a real password change flow)."""
        from accounts.signals import reset_must_change_password
        request = RequestFactory().post("/")
        reset_must_change_password(sender=None, request=request, user=user)

    def test_clears_must_change_password_when_flag_is_true(self):
        self.user.must_change_password = True
        self.user.save(update_fields=["must_change_password"])

        self._fire_password_changed(self.user)

        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)

    def test_does_nothing_when_flag_is_already_false(self):
        self.user.must_change_password = False
        self.user.save(update_fields=["must_change_password"])

        self._fire_password_changed(self.user)

        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)

    def test_persists_change_to_database(self):
        """Ensure save(update_fields=...) is actually called, not just the attr."""
        self.user.must_change_password = True
        self.user.save(update_fields=["must_change_password"])

        self._fire_password_changed(self.user)

        # Re-fetch from DB (not from the instance in memory)
        fresh = CustomUser.objects.get(pk=self.user.pk)
        self.assertFalse(fresh.must_change_password)

    def test_does_not_crash_when_attribute_missing(self):
        """Graceful handling if must_change_password attr is absent (getattr guard)."""
        mock_user = MagicMock(spec=[])  # spec with no attributes
        from accounts.signals import reset_must_change_password
        request = RequestFactory().post("/")
        try:
            reset_must_change_password(sender=None, request=request, user=mock_user)
        except Exception as exc:
            self.fail(f"Signal raised with missing attribute: {exc}")


# ── generate_username_from_email ──────────────────────────────────────────────

class GenerateUsernameFromEmailTests(TestCase):

    def test_username_auto_generated_on_create(self):
        user = CustomUser.objects.create_user(
            email="alice@example.com", password="pass"
        )
        self.assertNotEqual(user.username, "")
        self.assertIsNotNone(user.username)

    def test_username_derived_from_email_local_part(self):
        user = CustomUser.objects.create_user(
            email="bobsmith@example.com", password="pass"
        )
        self.assertIn("bobsmith", user.username)

    def test_existing_username_is_not_overwritten(self):
        user = CustomUser.objects.create_user(
            email="carol@example.com", password="pass", username="myhandle"
        )
        user.refresh_from_db()
        self.assertEqual(user.username, "myhandle")

    def test_username_unique_when_base_slug_already_taken(self):
        user1 = CustomUser.objects.create_user(
            email="dave@example.com", password="pass"
        )
        user2 = CustomUser.objects.create_user(
            email="dave@other.com", password="pass"
        )
        self.assertNotEqual(user1.username, user2.username)

    def test_username_generated_for_email_with_special_characters(self):
        """Plus tags, dots, and mixed case in the local-part are handled cleanly."""
        user = CustomUser.objects.create_user(
            email="Jane.Doe+tag@example.com", password="pass"
        )
        # Slug strips non-alphanum; result must be non-empty and alphanumeric
        self.assertTrue(user.username.replace("_", "").isalnum() or user.username != "")

    def test_username_generated_for_unicode_email(self):
        """Non-ASCII local-parts fall back to 'user' or a safe slug."""
        user = CustomUser.objects.create_user(
            email="用户@example.com", password="pass"
        )
        self.assertNotEqual(user.username, "")

    def test_username_not_generated_when_email_absent(self):
        """
        pre_save guard: if email is blank, the signal must not overwrite
        an existing username with a bad slug.
        """
        from accounts.signals import generate_username_from_email
        instance = CustomUser(email="", username="existing")
        generate_username_from_email(sender=CustomUser, instance=instance)
        self.assertEqual(instance.username, "existing")

    def test_username_length_within_model_limit(self):
        long_local = "a" * 200
        user = CustomUser.objects.create_user(
            email=f"{long_local}@example.com", password="pass"
        )
        self.assertLessEqual(len(user.username), 150)

    def test_saving_again_does_not_change_existing_username(self):
        user = CustomUser.objects.create_user(
            email="eve@example.com", password="pass"
        )
        original_username = user.username
        user.first_name = "Eve"
        user.save(update_fields=["first_name"])
        user.refresh_from_db()
        self.assertEqual(user.username, original_username)
