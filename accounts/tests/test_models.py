from django.db import IntegrityError

from accounts.models import CustomUser
from accounts.tests.base import AccountsBaseTestcase


class TestUserCreation(AccountsBaseTestcase):

    def test_create_user(self):
        self.assertIsNotNone(self.user)
        self.assertEqual(self.user.email, "testuser1@example.com")
        self.assertEqual(self.user.role, 'user')

        self.assertEqual(self.user.is_vendor, False)

        self.assertEqual(self.user.is_staff, False)
        self.assertEqual(self.user.is_superuser, False)

        self.assertEqual(self.user.must_change_password, False)
        self.assertEqual(self.user.disable_email_notification, False)

        self.assertEqual(self.user.is_content_vendor, False)

    def test_create_superuser(self):
        self.assertIsNotNone(self.admin)
        self.assertEqual(self.admin.email, "admin@example.com")
        self.assertEqual(self.admin.role, 'admin')
        self.assertEqual(self.admin.is_vendor, False)
        self.assertEqual(self.admin.is_staff, True)
        self.assertEqual(self.admin.is_superuser, True)

        self.assertEqual(self.admin.must_change_password, False)
        self.assertEqual(self.admin.disable_email_notification, False)
        self.assertEqual(self.admin.is_content_vendor, True)

    def test_create_vendor(self):
        self.assertIsNotNone(self.vendor)
        self.assertEqual(self.vendor.email, "vendor@example.com")
        self.assertEqual(self.vendor.role, 'vendor')

        self.assertEqual(self.vendor.is_vendor, True)

        self.assertEqual(self.vendor.is_staff, False)
        self.assertEqual(self.vendor.is_superuser, False)

        self.assertEqual(self.vendor.must_change_password, False)
        self.assertEqual(self.vendor.disable_email_notification, False)

        self.assertEqual(self.vendor.is_content_vendor, True)

    def test_username_is_derived_correctly_from_email(self):
        self.assertEqual(self.user.username, "testuser1")
        self.assertEqual(self.admin.username, "admin")
        self.assertEqual(self.vendor.username, "vendor")

    def test_unique_username(self):
        self.user2 = CustomUser.objects.create_user(
            email="testuser1@mail.com",
            password="password123",
        )
        self.assertEqual(self.user2.username, "testuser11")

    def test_derive_ascii_safe_username_from_email(self):
        self.user3 = CustomUser.objects.create_user(
            email="Jane.Doe+tag@example.com",
            password="password123",
        )
        self.assertEqual(self.user3.username, "janedoetag")

    def test_derive_ascii_safe_from_email_with_unicode_characters(self):
        self.user7 = CustomUser.objects.create_user(
            email="unicode测试文件🎉@example.com",
            password="password123",
        )
        self.assertEqual(self.user7.username, "unicode")

    def test_vendor_saved_with_vendor_role_has_the_is_vendor_toggled_on(self):
        self.user4 = CustomUser.objects.create_user(
            email="vendor2@gmail.com",
            password="password123",
            role=CustomUser.Role.VENDOR,
        )
        self.user5 = CustomUser.objects.create_user(
            email="vendor3@gmail.com",
            password="password123",
            is_vendor=True,
        )
        self.assertEqual(self.user4.is_vendor, True)
        self.assertEqual(self.user5.role, CustomUser.Role.VENDOR)

    def test_unique_email(self):
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(
                email="testuser1@example.com",
                password="password123",
            )

    def test_non_unique_username_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(
                email="testuser2@example.com",
                password="password123",
                username="testuser1",
            )

    def test_users_ordering(self):
        last_user = CustomUser.objects.last()
        first_user = CustomUser.objects.first()
        self.assertGreater(first_user.date_joined, last_user.date_joined)
