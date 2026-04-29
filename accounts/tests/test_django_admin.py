"""
accounts/tests/test_django_admin.py

Tests for the CustomUserAdmin registration and configuration.

Covers:
  - Admin site registration
  - list_display, list_filter, search_fields, ordering config
  - fieldsets and add_fieldsets structure
  - Admin changelist and change form rendering
  - Admin add form rendering and user creation
  - Search functionality
  - List filter functionality
"""
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from accounts.admin import CustomUserAdmin
from accounts.models import CustomUser
from accounts.tests.base import AccountsBaseTestcase


# ── Admin registration ────────────────────────────────────────────────────────

class CustomUserAdminRegistrationTests(AccountsBaseTestcase):

    def test_custom_user_is_registered_with_admin_site(self):
        from django.contrib import admin as django_admin
        self.assertIn(CustomUser, django_admin.site._registry)

    def test_registered_admin_class_is_custom_user_admin(self):
        from django.contrib import admin as django_admin
        self.assertIsInstance(django_admin.site._registry[CustomUser], CustomUserAdmin)


# ── ModelAdmin configuration ──────────────────────────────────────────────────

class CustomUserAdminConfigTests(AccountsBaseTestcase):
    """
    Unit-level checks against the ModelAdmin class attributes.
    No HTTP requests — just verify the metadata is correct.
    """

    def setUp(self):
        self.site = AdminSite()
        self.model_admin = CustomUserAdmin(CustomUser, self.site)

    # ── list_display ──────────────────────────────────────────────────────────

    def test_email_in_list_display(self):
        self.assertIn("email", self.model_admin.list_display)

    def test_role_in_list_display(self):
        self.assertIn("role", self.model_admin.list_display)

    def test_is_vendor_in_list_display(self):
        self.assertIn("is_vendor", self.model_admin.list_display)

    def test_must_change_password_in_list_display(self):
        self.assertIn("must_change_password", self.model_admin.list_display)

    def test_disable_email_notification_in_list_display(self):
        self.assertIn("disable_email_notification", self.model_admin.list_display)

    def test_date_joined_in_list_display(self):
        self.assertIn("date_joined", self.model_admin.list_display)

    def test_last_login_in_list_display(self):
        self.assertIn("last_login", self.model_admin.list_display)

    # ── list_filter ───────────────────────────────────────────────────────────

    def test_role_in_list_filter(self):
        self.assertIn("role", self.model_admin.list_filter)

    def test_is_vendor_in_list_filter(self):
        self.assertIn("is_vendor", self.model_admin.list_filter)

    def test_is_staff_in_list_filter(self):
        self.assertIn("is_staff", self.model_admin.list_filter)

    def test_is_active_in_list_filter(self):
        self.assertIn("is_active", self.model_admin.list_filter)

    def test_must_change_password_in_list_filter(self):
        self.assertIn("must_change_password", self.model_admin.list_filter)

    def test_disable_email_notification_in_list_filter(self):
        self.assertIn("disable_email_notification", self.model_admin.list_filter)

    # ── search_fields ─────────────────────────────────────────────────────────

    def test_email_in_search_fields(self):
        self.assertIn("email", self.model_admin.search_fields)

    def test_username_in_search_fields(self):
        self.assertIn("username", self.model_admin.search_fields)

    def test_first_name_in_search_fields(self):
        self.assertIn("first_name", self.model_admin.search_fields)

    def test_last_name_in_search_fields(self):
        self.assertIn("last_name", self.model_admin.search_fields)

    def test_phone_number_in_search_fields(self):
        self.assertIn("phone_number", self.model_admin.search_fields)

    # ── ordering ──────────────────────────────────────────────────────────────

    def test_ordering_is_descending_date_joined(self):
        self.assertEqual(self.model_admin.ordering, ("-date_joined",))

    # ── fieldsets ─────────────────────────────────────────────────────────────

    def _fieldset_fields(self):
        """Flatten all fields from all fieldsets into a single set."""
        fields = set()
        for _title, options in self.model_admin.fieldsets:
            for field in options.get("fields", []):
                fields.add(field)
        return fields

    def test_email_in_fieldsets(self):
        self.assertIn("email", self._fieldset_fields())

    def test_password_in_fieldsets(self):
        self.assertIn("password", self._fieldset_fields())

    def test_must_change_password_in_fieldsets(self):
        self.assertIn("must_change_password", self._fieldset_fields())

    def test_disable_email_notification_in_fieldsets(self):
        self.assertIn("disable_email_notification", self._fieldset_fields())

    def test_phone_number_in_fieldsets(self):
        self.assertIn("phone_number", self._fieldset_fields())

    def test_role_in_fieldsets(self):
        self.assertIn("role", self._fieldset_fields())

    def test_is_vendor_in_fieldsets(self):
        self.assertIn("is_vendor", self._fieldset_fields())

    def test_username_is_in_personal_info_fieldset(self):
        for title, options in self.model_admin.fieldsets:
            if "Personal info" in str(title):
                self.assertIn("username", options["fields"])
                return
        self.fail("Personal info fieldset not found")

    def test_permissions_fieldset_present(self):
        titles = [str(title) for title, _ in self.model_admin.fieldsets]
        self.assertTrue(any("Permissions" in t for t in titles))

    def test_important_dates_fieldset_present(self):
        titles = [str(title) for title, _ in self.model_admin.fieldsets]
        self.assertTrue(any("Important dates" in t for t in titles))

    # ── add_fieldsets ─────────────────────────────────────────────────────────

    def _add_fieldset_fields(self):
        fields = set()
        for _title, options in self.model_admin.add_fieldsets:
            for field in options.get("fields", []):
                fields.add(field)
        return fields

    def test_email_in_add_fieldsets(self):
        self.assertIn("email", self._add_fieldset_fields())

    def test_password1_in_add_fieldsets(self):
        self.assertIn("password1", self._add_fieldset_fields())

    def test_password2_in_add_fieldsets(self):
        self.assertIn("password2", self._add_fieldset_fields())

    def test_role_in_add_fieldsets(self):
        self.assertIn("role", self._add_fieldset_fields())

    def test_is_vendor_in_add_fieldsets(self):
        self.assertIn("is_vendor", self._add_fieldset_fields())

    def test_username_not_in_add_fieldsets(self):
        """Username is auto-generated — it must not appear in the add form."""
        self.assertNotIn("username", self._add_fieldset_fields())

    def test_add_fieldsets_have_wide_class(self):
        for _title, options in self.model_admin.add_fieldsets:
            self.assertIn("wide", options.get("classes", ()))


# ── HTTP / integration tests ──────────────────────────────────────────────────

class CustomUserAdminChangelistTests(AccountsBaseTestcase):
    """
    Admin views require a logged-in superuser.
    Uses self.admin (is_superuser=True) from the base testcase.
    """

    def setUp(self):
        self.login_as_admin()
        self.changelist_url = reverse("admin:accounts_customuser_changelist")

    def test_changelist_returns_200(self):
        response = self.client.get(self.changelist_url)
        self.assertEqual(response.status_code, 200)

    def test_changelist_lists_all_users(self):
        response = self.client.get(self.changelist_url)
        content = response.content.decode()
        self.assertIn(self.user.email, content)
        self.assertIn(self.vendor.email, content)
        self.assertIn(self.admin.email, content)

    def test_changelist_search_by_email(self):
        response = self.client.get(self.changelist_url, {"q": self.user.email})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.email)
        self.assertNotContains(response, self.vendor.email)

    def test_changelist_search_by_partial_email(self):
        response = self.client.get(self.changelist_url, {"q": "vendor"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.vendor.email)

    def test_changelist_filter_by_role_user(self):
        response = self.client.get(self.changelist_url, {"role": CustomUser.Role.USER})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.email)
        self.assertNotContains(response, self.vendor.email)

    def test_changelist_filter_by_role_vendor(self):
        response = self.client.get(self.changelist_url, {"role": CustomUser.Role.VENDOR})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.vendor.email)
        self.assertNotContains(response, self.user.email)

    def test_changelist_filter_by_is_vendor_true(self):
        response = self.client.get(self.changelist_url, {"is_vendor__exact": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.vendor.email)
        self.assertNotContains(response, self.user.email)

    def test_changelist_not_accessible_by_standard_user(self):
        self.login_as_user()
        response = self.client.get(self.changelist_url)
        self.assertIn(response.status_code, [302, 403])

    def test_changelist_not_accessible_by_vendor(self):
        self.login_as_vendor()
        response = self.client.get(self.changelist_url)
        self.assertIn(response.status_code, [302, 403])

    def test_changelist_not_accessible_anonymously(self):
        self.client.logout()
        response = self.client.get(self.changelist_url)
        self.assertIn(response.status_code, [302, 403])


class CustomUserAdminChangeFormTests(AccountsBaseTestcase):

    def setUp(self):
        self.login_as_admin()
        self.change_url = reverse("admin:accounts_customuser_change", args=[self.user.pk])

    def test_change_form_returns_200(self):
        response = self.client.get(self.change_url)
        self.assertEqual(response.status_code, 200)

    def test_change_form_contains_email_field(self):
        response = self.client.get(self.change_url)
        self.assertContains(response, 'name="email"')

    def test_change_form_contains_role_field(self):
        response = self.client.get(self.change_url)
        self.assertContains(response, 'name="role"')

    def test_change_form_contains_must_change_password_field(self):
        response = self.client.get(self.change_url)
        self.assertContains(response, 'name="must_change_password"')

    def test_change_form_contains_disable_email_notification_field(self):
        response = self.client.get(self.change_url)
        self.assertContains(response, 'name="disable_email_notification"')

    def test_change_form_for_nonexistent_user_returns_404(self):
        url = reverse("admin:accounts_customuser_change", args=[999999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_valid_post_updates_user(self):
        """POST the change form with a first_name update and verify it persists."""
        response = self.client.get(self.change_url)
        self.assertEqual(response.status_code, 200)

        # Build a minimal valid payload from the form's initial data
        form = response.context["adminform"].form
        data = {k: (v if not hasattr(v, "pk") else v.pk)
                for k, v in form.initial.items() if v is not None}

        data.update({
            "email": self.user.email,
            "first_name": "AdminEdited",
            "last_name": self.user.last_name or "",
            "username": self.user.username,
            "role": self.user.role,
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "is_vendor": False,
            "must_change_password": False,
            "disable_email_notification": False,
            "date_joined_0": self.user.date_joined.strftime("%Y-%m-%d"),
            "date_joined_1": self.user.date_joined.strftime("%H:%M:%S"),
            # ManyToMany — send empty
            "groups": [],
            "user_permissions": [],
            "favorites": [],
        })

        response = self.client.post(self.change_url, data=data)
        # Successful post redirects back to changelist
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "AdminEdited")


class CustomUserAdminAddFormTests(AccountsBaseTestcase):

    def setUp(self):
        self.login_as_admin()
        self.add_url = reverse("admin:accounts_customuser_add")

    def test_add_form_returns_200(self):
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 200)

    def test_add_form_does_not_contain_username_field(self):
        """Username is auto-generated; it should not be on the add form."""
        response = self.client.get(self.add_url)
        self.assertNotContains(response, 'name="username"')

    def test_add_form_contains_email_field(self):
        response = self.client.get(self.add_url)
        self.assertContains(response, 'name="email"')

    def test_add_form_contains_role_field(self):
        response = self.client.get(self.add_url)
        self.assertContains(response, 'name="role"')

    def test_valid_post_creates_user_and_redirects(self):
        data = {
            "email": "adminadd@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": CustomUser.Role.USER,
            "is_vendor": False,
        }
        response = self.client.post(self.add_url, data=data)
        # Django admin redirects to the change page of the new object on success
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(email="adminadd@example.com").exists())

    def test_valid_post_auto_generates_username(self):
        data = {
            "email": "autousername@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": CustomUser.Role.USER,
            "is_vendor": False,
        }
        self.client.post(self.add_url, data=data)
        user = CustomUser.objects.get(email="autousername@example.com")
        self.assertNotEqual(user.username, "")

    def test_mismatched_passwords_re_renders_form(self):
        data = {
            "email": "mismatch@example.com",
            "password1": "StrongPass123!",
            "password2": "WrongPass999!",
            "role": CustomUser.Role.USER,
            "is_vendor": False,
        }
        response = self.client.post(self.add_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email="mismatch@example.com").exists())

    def test_duplicate_email_re_renders_form(self):
        data = {
            "email": self.user.email,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": CustomUser.Role.USER,
            "is_vendor": False,
        }
        response = self.client.post(self.add_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.filter(email=self.user.email).count(), 1)
