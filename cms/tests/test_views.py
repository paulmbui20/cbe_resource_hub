from django.urls import reverse

from accounts.models import CustomUser
from cms.tests.base import CMSBaseTestCase


class TestCMSPageDetailView(CMSBaseTestCase):

    def _response(self):
        return self.client.get(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))

    def test_get_request(self):
        response = self._response()
        self.assertEqual(response.status_code, 200)

    def test_get_request_template_used(self):
        response = self._response()
        self.assertTemplateUsed(response, "cms/page_detail.html")

    def test_get_page_in_context(self):
        response = self._response()
        self.assertIn("page", response.context)

    def test_post_method_not_allowed(self):
        response = self.client.post(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))
        self.assertEqual(response.status_code, 405)

    def test_put_method_not_allowed(self):
        response = self.client.put(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))
        self.assertEqual(response.status_code, 405)

    def test_patch_method_not_allowed(self):
        response = self.client.patch(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))
        self.assertEqual(response.status_code, 405)

    def test_delete_method_not_allowed(self):
        response = self.client.delete(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))
        self.assertEqual(response.status_code, 405)

    def test_options_method_not_allowed(self):
        response = self.client.options(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))
        self.assertEqual(response.status_code, 405)

    def test_head_method_not_allowed(self):
        response = self.client.head(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))
        self.assertEqual(response.status_code, 405)

    def test_trace_method_not_allowed(self):
        response = self.client.trace(reverse("cms:page_detail", kwargs={"slug": self.page.slug}))
        self.assertEqual(response.status_code, 405)

    def test_get_is_accessible_to_logged_in_user(self):
        self.user = CustomUser.objects.create_user(
            email="anon@example.com",
            password="password123",
        )
        self.client.force_login(self.user)

        response = self._response()
        self.assertEqual(response.status_code, 200)

    def test_get_is_accessible_to_logged_in_admin_user(self):
        self.admin = CustomUser.objects.create_superuser(
            email="anonadmin@example.com",
            password="password123",
        )
        self.client.force_login(self.admin)

        response = self._response()
        self.assertEqual(response.status_code, 200)

    def test_get_is_accessible_to_logged_in_vendor_user(self):
        self.vendor = CustomUser.objects.create_superuser(
            email="anonvendor@example.com",
            password="password123",
            role=CustomUser.Role.VENDOR,
            is_vendor=True,
        )
        self.client.force_login(self.vendor)

        response = self._response()
        self.assertEqual(response.status_code, 200)
