"""
accounts/tests/test_adapters.py

Tests for accounts/adapters.py that are NOT already covered by test_models.py.

test_models.py already covers (via model creation):
  - _slugify_username: normal email, plus-tag, Unicode, dots, mixed case
  - _unique_username: suffix increment when base is taken
  - AccountAdapter.populate_username / save_user: implicit via create_user

This file covers the remaining gaps:
  - _slugify_username: edge cases (all non-ascii, empty local-part, digits)
  - _unique_username: counter increments past 1, very long base slug truncation
  - AccountAdapter.populate_username: called on a user object directly
  - AccountAdapter.save_user: commit=False path, username fallback when missing
  - SocialAccountAdapter.pre_social_login: existing user, no email, unknown email
  - SocialAccountAdapter.populate_user: name fields copied, username generated
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, RequestFactory

from accounts.adapters import (
    AccountAdapter,
    SocialAccountAdapter,
    _slugify_username,
    _unique_username,
)
from accounts.models import CustomUser
from accounts.tests.base import AccountsBaseTestcase


# ── _slugify_username ─────────────────────────────────────────────────────────

class SlugifyUsernameTests(TestCase):

    def test_simple_email_returns_local_part(self):
        self.assertEqual(_slugify_username("alice@example.com"), "alice")

    def test_uppercase_is_lowercased(self):
        self.assertEqual(_slugify_username("ALICE@example.com"), "alice")

    def test_dots_stripped(self):
        self.assertEqual(_slugify_username("alice.smith@example.com"), "alicesmith")

    def test_plus_tag_stripped(self):
        self.assertEqual(_slugify_username("alice+tag@example.com"), "alicetag")

    def test_digits_preserved(self):
        self.assertEqual(_slugify_username("user123@example.com"), "user123")

    def test_all_non_ascii_local_part_falls_back_to_user(self):
        # A purely non-ASCII local-part that produces an empty slug → "user"
        self.assertEqual(_slugify_username("🎉🎊@example.com"), "user")

    def test_empty_string_falls_back_to_user(self):
        # Edge case: empty local-part after stripping
        self.assertEqual(_slugify_username("@example.com"), "user")

    def test_mixed_ascii_and_unicode_keeps_ascii_portion(self):
        # "unicode测试" → "unicode" after stripping non-ascii
        result = _slugify_username("unicode测试@example.com")
        self.assertEqual(result, "unicode")

    def test_hyphen_stripped(self):
        # Hyphens are not alphanumeric so they are removed
        result = _slugify_username("alice-smith@example.com")
        self.assertEqual(result, "alicesmith")

    def test_local_part_with_only_digits(self):
        result = _slugify_username("12345@example.com")
        self.assertEqual(result, "12345")


# ── _unique_username ──────────────────────────────────────────────────────────

class UniqueUsernameTests(TestCase):

    def test_returns_base_when_no_collision(self):
        result = _unique_username("freshslug")
        self.assertEqual(result, "freshslug")

    def test_returns_base1_when_base_taken(self):
        CustomUser.objects.create_user(email="base@example.com", password="pass", username="base")
        result = _unique_username("base")
        self.assertEqual(result, "base1")

    def test_increments_past_1_when_base1_also_taken(self):
        CustomUser.objects.create_user(email="c1@example.com", password="pass", username="counter")
        CustomUser.objects.create_user(email="c2@example.com", password="pass", username="counter1")
        result = _unique_username("counter")
        self.assertEqual(result, "counter2")

    def test_increments_past_2(self):
        CustomUser.objects.create_user(email="d1@example.com", password="pass", username="dup")
        CustomUser.objects.create_user(email="d2@example.com", password="pass", username="dup1")
        CustomUser.objects.create_user(email="d3@example.com", password="pass", username="dup2")
        result = _unique_username("dup")
        self.assertEqual(result, "dup3")

    def test_long_base_is_truncated_to_148_chars(self):
        long_base = "a" * 200
        result = _unique_username(long_base)
        # The candidate is sliced to 148 before the uniqueness check
        self.assertLessEqual(len(result), 150)

    def test_truncated_base_with_suffix_stays_within_150(self):
        long_base = "b" * 200
        # Force a collision on the truncated slug so a suffix is appended
        truncated = long_base[:148]
        CustomUser.objects.create_user(
            email="long@example.com", password="pass", username=truncated
        )
        result = _unique_username(long_base)
        self.assertLessEqual(len(result), 150)

    def test_result_is_unique_in_database(self):
        CustomUser.objects.create_user(email="u1@example.com", password="pass", username="myslug")
        result = _unique_username("myslug")
        self.assertFalse(CustomUser.objects.filter(username=result).exists())


# ── AccountAdapter ────────────────────────────────────────────────────────────

class AccountAdapterPopulateUsernameTests(TestCase):

    def setUp(self):
        self.adapter = AccountAdapter()
        self.request = RequestFactory().get("/")

    def test_populate_username_sets_username_from_email(self):
        user = CustomUser(email="populate@example.com")
        self.adapter.populate_username(self.request, user)
        self.assertEqual(user.username, "populate")

    def test_populate_username_handles_plus_tag(self):
        user = CustomUser(email="first+tag@example.com")
        self.adapter.populate_username(self.request, user)
        self.assertEqual(user.username, "firsttag")

    def test_populate_username_generates_unique_slug(self):
        CustomUser.objects.create_user(
            email="taken@example.com", password="pass", username="taken"
        )
        user = CustomUser(email="taken@other.com")
        self.adapter.populate_username(self.request, user)
        self.assertEqual(user.username, "taken1")

    def test_populate_username_does_not_save_user(self):
        """populate_username only mutates the instance — no DB write."""
        user = CustomUser(email="nosave@example.com")
        self.adapter.populate_username(self.request, user)
        self.assertFalse(CustomUser.objects.filter(email="nosave@example.com").exists())


class AccountAdapterSaveUserTests(TestCase):

    def setUp(self):
        self.adapter = AccountAdapter()
        self.request = RequestFactory().post("/")

    def _make_form(self, cleaned_data):
        form = MagicMock()
        form.cleaned_data = cleaned_data
        return form

    def test_save_user_with_commit_false_does_not_persist(self):
        form = self._make_form({"email": "commitfalse@example.com", "password1": "pass"})
        # Patch super().save_user to return a bare user instance
        user = CustomUser(email="commitfalse@example.com")
        with patch(
                "allauth.account.adapter.DefaultAccountAdapter.save_user",
                return_value=user,
        ):
            result = self.adapter.save_user(self.request, user, form, commit=False)
        self.assertFalse(CustomUser.objects.filter(email="commitfalse@example.com").exists())
        # Username should still be populated even with commit=False
        self.assertNotEqual(result.username, "")

    def test_save_user_generates_username_when_missing(self):
        """If super().save_user returns a user with no username, the adapter fills it."""
        user = CustomUser(email="nousername@example.com", username="")
        form = self._make_form({"email": "nousername@example.com", "password1": "pass"})
        with patch(
                "allauth.account.adapter.DefaultAccountAdapter.save_user",
                return_value=user,
        ):
            result = self.adapter.save_user(self.request, user, form, commit=False)
        self.assertNotEqual(result.username, "")
        self.assertIn("nousername", result.username)


# ── SocialAccountAdapter ──────────────────────────────────────────────────────

class SocialAccountAdapterPreSocialLoginTests(AccountsBaseTestcase):

    def setUp(self):
        self.adapter = SocialAccountAdapter()
        self.request = RequestFactory().get("/")

    def _make_sociallogin(self, email="", is_existing=False):
        sociallogin = MagicMock()
        sociallogin.is_existing = is_existing
        sociallogin.account.extra_data = {"email": email}
        return sociallogin

    def test_does_nothing_when_sociallogin_already_existing(self):
        """If the social account is already connected, skip the lookup."""
        sociallogin = self._make_sociallogin(email=self.user.email, is_existing=True)
        self.adapter.pre_social_login(self.request, sociallogin)
        sociallogin.connect.assert_not_called()

    def test_connects_social_login_to_existing_user_with_matching_email(self):
        sociallogin = self._make_sociallogin(email=self.user.email, is_existing=False)
        self.adapter.pre_social_login(self.request, sociallogin)
        sociallogin.connect.assert_called_once_with(self.request, self.user)

    def test_does_nothing_when_email_is_empty(self):
        sociallogin = self._make_sociallogin(email="", is_existing=False)
        self.adapter.pre_social_login(self.request, sociallogin)
        sociallogin.connect.assert_not_called()

    def test_does_nothing_when_no_matching_user_found(self):
        sociallogin = self._make_sociallogin(
            email="ghost@nowhere.invalid", is_existing=False
        )
        self.adapter.pre_social_login(self.request, sociallogin)
        sociallogin.connect.assert_not_called()

    def test_email_lookup_is_case_insensitive(self):
        """Lower-strips the email before lookup — uppercase version should still match."""
        sociallogin = self._make_sociallogin(
            email=self.user.email.upper(), is_existing=False
        )
        self.adapter.pre_social_login(self.request, sociallogin)
        sociallogin.connect.assert_called_once_with(self.request, self.user)


class SocialAccountAdapterPopulateUserTests(TestCase):

    def setUp(self):
        self.adapter = SocialAccountAdapter()
        self.request = RequestFactory().get("/")

    def _make_sociallogin(self):
        return MagicMock()

    def _call_populate(self, data, existing_first="", existing_last="", existing_username=""):
        sociallogin = self._make_sociallogin()
        user = MagicMock()
        user.first_name = existing_first
        user.last_name = existing_last
        user.username = existing_username
        user.email = data.get("email", "")

        with patch(
                "allauth.socialaccount.adapter.DefaultSocialAccountAdapter.populate_user",
                return_value=user,
        ):
            return self.adapter.populate_user(self.request, sociallogin, data)

    def test_copies_first_name_from_social_data(self):
        result = self._call_populate(
            {"email": "g@example.com", "first_name": "Google", "last_name": "User"},
            existing_first="",
        )
        self.assertEqual(result.first_name, "Google")

    def test_copies_last_name_from_social_data(self):
        result = self._call_populate(
            {"email": "g@example.com", "first_name": "Google", "last_name": "User"},
            existing_last="",
        )
        self.assertEqual(result.last_name, "User")

    def test_does_not_overwrite_existing_first_name(self):
        result = self._call_populate(
            {"email": "g@example.com", "first_name": "Google", "last_name": "User"},
            existing_first="Already",
        )
        self.assertEqual(result.first_name, "Already")

    def test_does_not_overwrite_existing_last_name(self):
        result = self._call_populate(
            {"email": "g@example.com", "first_name": "Google", "last_name": "User"},
            existing_last="Set",
        )
        self.assertEqual(result.last_name, "Set")

    def test_generates_username_when_missing(self):
        result = self._call_populate(
            {"email": "newgoogle@example.com", "first_name": "G", "last_name": "U"},
            existing_username="",
        )
        self.assertNotEqual(result.username, "")

    def test_does_not_overwrite_existing_username(self):
        result = self._call_populate(
            {"email": "g@example.com", "first_name": "G", "last_name": "U"},
            existing_username="myhandle",
        )
        self.assertEqual(result.username, "myhandle")

    def test_handles_missing_first_name_in_social_data_gracefully(self):
        result = self._call_populate(
            {"email": "g@example.com", "last_name": "Only"},
            existing_first="",
        )
        # first_name should default to empty string, not raise
        self.assertEqual(result.first_name, "")

    def test_handles_missing_last_name_in_social_data_gracefully(self):
        result = self._call_populate(
            {"email": "g@example.com", "first_name": "Only"},
            existing_last="",
        )
        self.assertEqual(result.last_name, "")
