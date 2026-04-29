from django.conf import settings
from django.urls import reverse

from accounts.models import CustomUser
from accounts.tests.base import AccountsBaseTestcase


class AccountsProfileViewTests(AccountsBaseTestcase):

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"{getattr(settings, 'LOGIN_URL')}", response.url)

    def test_logged_in_user_can_access_profile_page(self):
        self.login_as_user()
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertIn("user", response.context)
        self.assertIn("form", response.context)

    def test_logged_in_admin_user_can_access_profile_page(self):
        self.login_as_admin()
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertIn("user", response.context)
        self.assertIn("form", response.context)

    def test_logged_in_vendor_user_can_access_profile_page(self):
        self.login_as_vendor()
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertIn("user", response.context)
        self.assertIn("form", response.context)

    def test_profile_page_post(self):
        self.login_as_user()

        form_data = {"first_name": "Johny", "last_name": "Doe", "phone_number": "+254712345670",
                     "disable_email_notification": True, }

        response = self.client.post(reverse("accounts:profile"), data=form_data)
        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "Johny")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertEqual(self.user.phone_number, "+254712345670")
        self.assertEqual(self.user.disable_email_notification, True)


class AccountsBecomeVendorViewTests(AccountsBaseTestcase):

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.post(reverse("accounts:become_vendor"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"{getattr(settings, 'LOGIN_URL')}", response.url)

    def test_returns_forbidden_method_on_get(self):
        self.login_as_user()
        response = self.client.get(reverse("accounts:become_vendor"))
        self.assertEqual(response.status_code, 405)

    def test_logged_in_user_can_upgrade_to_a_vendor(self):
        self.login_as_user()
        response = self.client.post(reverse("accounts:become_vendor"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"{reverse("accounts:dashboard")}", response.url)

        self.user.refresh_from_db()

        self.assertEqual(self.user.role, CustomUser.Role.VENDOR)
        self.assertEqual(self.user.is_vendor, True)
        self.assertEqual(self.user.is_content_vendor, True)

    def test_logged_in_admin_cannot_upgrade_to_a_vendor_since_they_are_already_privileged(self):
        self.login_as_admin()
        response = self.client.post(reverse("accounts:become_vendor"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"{reverse("accounts:dashboard")}", response.url)

        self.admin.refresh_from_db()

        self.assertEqual(self.admin.role, CustomUser.Role.ADMIN)
        self.assertEqual(self.admin.is_vendor, False)
        self.assertEqual(self.admin.is_content_vendor, True)

    def test_logged_in_vendor_cannot_upgrade_to_a_vendor_since_they_are_already_one(self):
        self.login_as_vendor()
        response = self.client.post(reverse("accounts:become_vendor"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"{reverse("accounts:dashboard")}", response.url)

        self.vendor.refresh_from_db()

        self.assertEqual(self.vendor.role, CustomUser.Role.VENDOR)
        self.assertEqual(self.vendor.is_vendor, True)
        self.assertEqual(self.vendor.is_content_vendor, True)


class AccountsDashboardViewTests(AccountsBaseTestcase):

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"{getattr(settings, 'LOGIN_URL')}", response.url)

    def test_logged_in_user_can_access_dashboard(self):
        self.login_as_user()
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "accounts/dashboard.html")

        self.assertIn("user", response.context)
        self.assertIn("my_resources", response.context)
        self.assertIn("my_resource_count", response.context)
        self.assertIn("my_favorites", response.context)
        self.assertIn("my_favorites_count", response.context)
        self.assertIn("email_verified", response.context)

        self.assertEqual(response.context["user"].role, CustomUser.Role.USER)

        self.assertEqual(response.context["email_verified"], False)

    def test_logged_in_admin_can_access_dashboard(self):
        self.login_as_admin()
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "accounts/dashboard.html")

        self.assertIn("user", response.context)
        self.assertIn("my_resources", response.context)
        self.assertIn("my_resource_count", response.context)
        self.assertIn("my_favorites", response.context)
        self.assertIn("my_favorites_count", response.context)
        self.assertIn("email_verified", response.context)

        self.assertEqual(response.context["user"].role, CustomUser.Role.ADMIN)

        self.assertEqual(response.context["email_verified"], True)

    def test_logged_in_vendor_can_access_dashboard(self):
        self.login_as_vendor()
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "accounts/dashboard.html")

        self.assertIn("user", response.context)
        self.assertIn("my_resources", response.context)
        self.assertIn("my_resource_count", response.context)
        self.assertIn("my_favorites", response.context)
        self.assertIn("my_favorites_count", response.context)
        self.assertIn("email_verified", response.context)

        self.assertEqual(response.context["user"].role, CustomUser.Role.VENDOR)

        self.assertEqual(response.context["email_verified"], False)
