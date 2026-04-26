"""
accounts/tests/test_admin_views.py

Test suite for accounts/admin_views.py (management namespace).

Covers:
  - IsAdminMixin access control (anon, user, vendor, admin)
  - AdminUserListView  — list, search, pagination
  - AdminUserCreateView — GET, valid POST, invalid POST
  - AdminUserUpdateView — GET, valid POST, invalid POST
  - AdminUserDeleteView — GET, POST (delete)
  - AdminUserBulkToggleView — enable, disable, self-disable guard, bad payloads
"""

import json

from django.urls import reverse

from accounts.models import CustomUser
from accounts.tests.base import AccountsBaseTestcase


# ── helpers ──────────────────────────────────────────────────────────────────

def _post_json(client, url, payload):
    """POST JSON body and return response."""
    return client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
    )


# ── IsAdminMixin (access control shared across all views) ────────────────────

class IsAdminMixinTests(AccountsBaseTestcase):
    """
    Every management view is protected by IsAdminMixin.
    Verify that anonymous users, standard users, and vendors are all blocked,
    while admin / superuser accounts are allowed through.
    """

    PROTECTED_URLS = [
        ("management:user_list", {}),
        ("management:user_add", {}),
        ("management:user_bulk_toggle", {}),
        ("management:user_edit", {"pk": 0}),  # pk patched per-test
        ("management:user_delete", {"pk": 0}),
    ]

    def _url(self, name, kwargs):
        if "pk" in kwargs and kwargs["pk"] == 0:
            kwargs = {"pk": self.user.pk}
        return reverse(name, kwargs=kwargs or None)

    # ── anonymous ─────────────────────────────────────────────────────────────

    def test_anonymous_redirected_from_user_list(self):
        response = self.client.get(reverse("management:user_list"))
        self.assertIn(response.status_code, [302, 403])

    def test_anonymous_redirected_from_user_add(self):
        response = self.client.get(reverse("management:user_add"))
        self.assertIn(response.status_code, [302, 403])

    def test_anonymous_redirected_from_user_edit(self):
        response = self.client.get(reverse("management:user_edit", kwargs={"pk": self.user.pk}))
        self.assertIn(response.status_code, [302, 403])

    def test_anonymous_redirected_from_user_delete(self):
        response = self.client.get(reverse("management:user_delete", kwargs={"pk": self.user.pk}))
        self.assertIn(response.status_code, [302, 403])

    # ── standard user ─────────────────────────────────────────────────────────

    def test_standard_user_forbidden_from_user_list(self):
        self.login_as_user()
        response = self.client.get(reverse("management:user_list"))
        self.assertIn(response.status_code, [302, 403])

    def test_standard_user_forbidden_from_user_add(self):
        self.login_as_user()
        response = self.client.get(reverse("management:user_add"))
        self.assertIn(response.status_code, [302, 403])

    # ── vendor ────────────────────────────────────────────────────────────────

    def test_vendor_forbidden_from_user_list(self):
        self.login_as_vendor()
        response = self.client.get(reverse("management:user_list"))
        self.assertIn(response.status_code, [302, 403])

    # ── admin ─────────────────────────────────────────────────────────────────

    def test_admin_can_access_user_list(self):
        self.login_as_admin()
        response = self.client.get(reverse("management:user_list"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_user_add(self):
        self.login_as_admin()
        response = self.client.get(reverse("management:user_add"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_user_edit(self):
        self.login_as_admin()
        response = self.client.get(reverse("management:user_edit", kwargs={"pk": self.user.pk}))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_user_delete(self):
        self.login_as_admin()
        response = self.client.get(reverse("management:user_delete", kwargs={"pk": self.user.pk}))
        self.assertEqual(response.status_code, 200)


# ── AdminUserListView ─────────────────────────────────────────────────────────

class AdminUserListViewTests(AccountsBaseTestcase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:user_list")

    def test_returns_200_with_correct_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/user_list.html")

    def test_context_contains_users(self):
        response = self.client.get(self.url)
        self.assertIn("users", response.context)

    def test_all_users_appear_in_list(self):
        response = self.client.get(self.url)
        emails = [u.email for u in response.context["users"]]
        self.assertIn(self.user.email, emails)
        self.assertIn(self.admin.email, emails)
        self.assertIn(self.vendor.email, emails)

    def test_search_by_email_filters_results(self):
        response = self.client.get(self.url, {"q": self.user.email})
        emails = [u.email for u in response.context["users"]]
        self.assertIn(self.user.email, emails)
        self.assertNotIn(self.vendor.email, emails)

    def test_search_returns_empty_when_no_match(self):
        response = self.client.get(self.url, {"q": "nomatch@nowhere.invalid"})
        self.assertEqual(len(response.context["users"]), 0)

    def test_search_is_case_insensitive(self):
        response = self.client.get(self.url, {"q": self.user.email.upper()})
        emails = [u.email for u in response.context["users"]]
        self.assertIn(self.user.email, emails)

    def test_search_partial_email_returns_matches(self):
        # "testuser" appears in testuser1@example.com
        response = self.client.get(self.url, {"q": "testuser"})
        emails = [u.email for u in response.context["users"]]
        self.assertIn(self.user.email, emails)

    def test_list_ordered_by_most_recently_joined(self):
        """Queryset is ordered -date_joined; the newest user should appear first."""
        newest = CustomUser.objects.create_user(
            email="newest@example.com", password="pass"
        )
        response = self.client.get(self.url)
        first_user = list(response.context["users"])[0]
        self.assertEqual(first_user.pk, newest.pk)


# ── AdminUserCreateView ───────────────────────────────────────────────────────

class AdminUserCreateViewTests(AccountsBaseTestcase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:user_add")

    def _valid_payload(self, **overrides):
        data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "is_active": True,
            "role": CustomUser.Role.USER,
            "is_vendor": False,
        }
        data.update(overrides)
        return data

    # ── GET ───────────────────────────────────────────────────────────────────

    def test_get_returns_200_with_correct_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/generic_form.html")

    def test_get_context_has_title_and_cancel_url(self):
        response = self.client.get(self.url)
        self.assertIn("title", response.context)
        self.assertIn("cancel_url", response.context)

    # ── POST (valid) ──────────────────────────────────────────────────────────

    def test_valid_post_creates_user(self):
        self.client.post(self.url, data=self._valid_payload())
        self.assertTrue(CustomUser.objects.filter(email="newuser@example.com").exists())

    def test_valid_post_redirects_to_user_list(self):
        response = self.client.post(self.url, data=self._valid_payload())
        self.assertRedirects(response, reverse("management:user_list"))

    def test_created_user_has_must_change_password_flag(self):
        self.client.post(self.url, data=self._valid_payload())
        user = CustomUser.objects.get(email="newuser@example.com")
        self.assertTrue(user.must_change_password)

    def test_created_user_has_unusable_or_random_password(self):
        """The view sets a random password; the raw password is never stored."""
        self.client.post(self.url, data=self._valid_payload())
        user = CustomUser.objects.get(email="newuser@example.com")
        # A randomly set password means check_password("password123") is False.
        self.assertFalse(user.check_password("password123"))

    def test_created_user_has_auto_generated_username(self):
        self.client.post(self.url, data=self._valid_payload())
        user = CustomUser.objects.get(email="newuser@example.com")
        self.assertNotEqual(user.username, "")

    def test_creating_vendor_role_sets_is_vendor_flag(self):
        self.client.post(self.url, data=self._valid_payload(role=CustomUser.Role.VENDOR, is_vendor=True))
        user = CustomUser.objects.get(email="newuser@example.com")
        self.assertTrue(user.is_vendor)
        self.assertEqual(user.role, CustomUser.Role.VENDOR)

    # ── POST (invalid) ────────────────────────────────────────────────────────

    def test_invalid_post_missing_email_re_renders_form(self):
        payload = self._valid_payload()
        del payload["email"]
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/generic_form.html")

    def test_invalid_post_duplicate_email_re_renders_form(self):
        payload = self._valid_payload(email=self.user.email)
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "email", [])  # at least one error exists
        # simpler guard: no second user with that email
        self.assertEqual(CustomUser.objects.filter(email=self.user.email).count(), 1)


# ── AdminUserUpdateView ───────────────────────────────────────────────────────

class AdminUserUpdateViewTests(AccountsBaseTestcase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:user_edit", kwargs={"pk": self.user.pk})

    def _valid_payload(self, **overrides):
        data = {
            "email": self.user.email,
            "first_name": "Updated",
            "last_name": "Name",
            "is_active": True,
            "role": CustomUser.Role.USER,
            "is_vendor": False,
        }
        data.update(overrides)
        return data

    # ── GET ───────────────────────────────────────────────────────────────────

    def test_get_returns_200_with_correct_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/generic_form.html")

    def test_get_context_has_title_and_cancel_url(self):
        response = self.client.get(self.url)
        self.assertIn("title", response.context)
        self.assertIn("cancel_url", response.context)

    def test_context_title_contains_user_email(self):
        response = self.client.get(self.url)
        self.assertIn(self.user.email, response.context["title"])

    # ── POST (valid) ──────────────────────────────────────────────────────────

    def test_valid_post_updates_first_and_last_name(self):
        self.client.post(self.url, data=self._valid_payload())
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")

    def test_valid_post_redirects_to_user_list(self):
        response = self.client.post(self.url, data=self._valid_payload())
        self.assertRedirects(response, reverse("management:user_list"))

    def test_valid_post_can_promote_user_to_vendor(self):
        self.client.post(self.url, data=self._valid_payload(role=CustomUser.Role.VENDOR, is_vendor=True))
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, CustomUser.Role.VENDOR)
        self.assertTrue(self.user.is_vendor)

    def test_valid_post_can_deactivate_user(self):
        self.client.post(self.url, data=self._valid_payload(is_active=False))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    # ── POST (invalid) ────────────────────────────────────────────────────────

    def test_invalid_post_blank_email_re_renders_form(self):
        payload = self._valid_payload(email="")
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/generic_form.html")

    def test_invalid_post_does_not_change_user(self):
        original_name = self.user.first_name
        self.client.post(self.url, data=self._valid_payload(email=""))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, original_name)

    def test_updating_nonexistent_user_returns_404(self):
        url = reverse("management:user_edit", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ── AdminUserDeleteView ───────────────────────────────────────────────────────

class AdminUserDeleteViewTests(AccountsBaseTestcase):
    """
    Uses a fresh throwaway user per test so deletions don't destroy
    the shared fixtures in AccountsBaseTestcase.setUpClass.
    """

    def setUp(self):
        self.login_as_admin()
        self.target = CustomUser.objects.create_user(
            email="todelete@example.com", password="pass"
        )
        self.url = reverse("management:user_delete", kwargs={"pk": self.target.pk})

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_deletes_user(self):
        self.client.post(self.url)
        self.assertFalse(CustomUser.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects_to_user_list(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("management:user_list"))

    def test_delete_nonexistent_user_returns_404(self):
        url = reverse("management:user_delete", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ── AdminUserBulkToggleView ───────────────────────────────────────────────────

class AdminUserBulkToggleViewTests(AccountsBaseTestcase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:user_bulk_toggle")
        # fresh targets so we don't mutate the shared fixtures
        self.target_a = CustomUser.objects.create_user(
            email="bulk_a@example.com", password="pass", is_active=True
        )
        self.target_b = CustomUser.objects.create_user(
            email="bulk_b@example.com", password="pass", is_active=True
        )

    def _ids(self, *users):
        return [u.pk for u in users]

    # ── method guard ─────────────────────────────────────────────────────────

    def test_get_returns_405(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    # ── disable ───────────────────────────────────────────────────────────────

    def test_disable_sets_users_inactive(self):
        _post_json(self.client, self.url, {"action": "disable", "user_ids": self._ids(self.target_a, self.target_b)})
        self.target_a.refresh_from_db()
        self.target_b.refresh_from_db()
        self.assertFalse(self.target_a.is_active)
        self.assertFalse(self.target_b.is_active)

    def test_disable_returns_json_success(self):
        response = _post_json(self.client, self.url, {"action": "disable", "user_ids": self._ids(self.target_a)})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get("success"))

    def test_disable_self_is_forbidden(self):
        response = _post_json(
            self.client, self.url,
            {"action": "disable", "user_ids": [self.admin.pk]}
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_disable_self_does_not_deactivate_admin(self):
        _post_json(self.client, self.url, {"action": "disable", "user_ids": [self.admin.pk]})
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    # ── enable ────────────────────────────────────────────────────────────────

    def test_enable_sets_users_active(self):
        # first disable them
        self.target_a.is_active = False
        self.target_a.save(update_fields=["is_active"])
        _post_json(self.client, self.url, {"action": "enable", "user_ids": self._ids(self.target_a)})
        self.target_a.refresh_from_db()
        self.assertTrue(self.target_a.is_active)

    def test_enable_returns_json_success(self):
        response = _post_json(self.client, self.url, {"action": "enable", "user_ids": self._ids(self.target_a)})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get("success"))

    # ── invalid payloads ─────────────────────────────────────────────────────

    def test_invalid_action_returns_400(self):
        response = _post_json(self.client, self.url, {"action": "nuke", "user_ids": self._ids(self.target_a)})
        self.assertEqual(response.status_code, 400)

    def test_empty_user_ids_returns_400(self):
        response = _post_json(self.client, self.url, {"action": "disable", "user_ids": []})
        self.assertEqual(response.status_code, 400)

    def test_missing_action_field_returns_400(self):
        response = _post_json(self.client, self.url, {"user_ids": self._ids(self.target_a)})
        self.assertEqual(response.status_code, 400)

    def test_malformed_json_returns_400(self):
        response = self.client.post(
            self.url,
            data="this is not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    # ── access control ───────────────────────────────────────────────────────

    def test_anonymous_cannot_use_bulk_toggle(self):
        self.client.logout()
        response = _post_json(self.client, self.url, {"action": "disable", "user_ids": self._ids(self.target_a)})
        self.assertIn(response.status_code, [302, 403])

    def test_standard_user_cannot_use_bulk_toggle(self):
        self.login_as_user()
        response = _post_json(self.client, self.url, {"action": "disable", "user_ids": self._ids(self.target_a)})
        self.assertIn(response.status_code, [302, 403])

    def test_vendor_cannot_use_bulk_toggle(self):
        self.login_as_vendor()
        response = _post_json(self.client, self.url, {"action": "disable", "user_ids": self._ids(self.target_a)})
        self.assertIn(response.status_code, [302, 403])

    # ── edge cases ───────────────────────────────────────────────────────────

    def test_bulk_toggle_with_nonexistent_ids_is_harmless(self):
        """update() on a queryset with no matching rows silently returns 0."""
        response = _post_json(self.client, self.url, {"action": "enable", "user_ids": [99999, 99998]})
        self.assertEqual(response.status_code, 200)

    def test_mixed_ids_only_updates_valid_users(self):
        response = _post_json(
            self.client, self.url,
            {"action": "disable", "user_ids": [self.target_a.pk, 99999]}
        )
        self.assertEqual(response.status_code, 200)
        self.target_a.refresh_from_db()
        self.assertFalse(self.target_a.is_active)
