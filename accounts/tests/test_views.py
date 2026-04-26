from django.conf import settings
from django.urls import reverse

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
