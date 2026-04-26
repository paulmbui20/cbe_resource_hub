from django.test import TestCase

from accounts.models import CustomUser


class AccountsBaseTestcase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = CustomUser.objects.create_user(
            email="testuser1@example.com",
            password="password123",
        )
        cls.admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="password123",
        )
        cls.vendor = CustomUser.objects.create_user(
            email="vendor@example.com",
            password="password123",
            role=CustomUser.Role.VENDOR,
            is_vendor=True
        )

    def login_as_admin(self):
        """Log in as admin user"""
        self.client.force_login(self.admin)

    def login_as_vendor(self):
        """Log in as vendor user"""
        self.client.force_login(self.vendor)

    def login_as_user(self):
        """Log in as user"""
        self.client.force_login(self.user)
