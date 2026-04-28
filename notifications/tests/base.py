"""
notifications/tests/base.py

Shared fixtures for all notification tests.
"""

from django.test import TestCase

from accounts.models import CustomUser
from notifications.models import Notification


class NotificationBaseTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = CustomUser.objects.create_superuser(
            email="notif_admin@example.com", password="pass123"
        )
        cls.staff = CustomUser.objects.create_user(
            email="notif_staff@example.com",
            password="pass123",
            is_staff=True,
        )
        cls.regular_user = CustomUser.objects.create_user(
            email="notif_user@example.com", password="pass123"
        )

    def login_as_admin(self):
        self.client.force_login(self.admin)

    def login_as_staff(self):
        self.client.force_login(self.staff)

    def login_as_user(self):
        self.client.force_login(self.regular_user)

    @staticmethod
    def make_notification(**kwargs):
        defaults = dict(
            notification_type=Notification.Type.GENERAL,
            recipient_email="recipient@example.com",
            subject="Test Subject",
            content_text="Plain text body.",
            content_html="<p>HTML body.</p>",
            status=Notification.Status.PENDING,
        )
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)
