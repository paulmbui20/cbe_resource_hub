"""
notifications/tests/test_models.py

Model tests for Notification:
  - Creation with each Type and Status choice
  - Default values
  - Idempotency key uniqueness
  - Nullable / blank field behaviour
  - __str__ representation
  - Ordering (newest first)
  - metadata JSONField defaults
  - retry_count default
"""

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from notifications.models import Notification
from notifications.tests.base import NotificationBaseTestCase


class NotificationCreationTests(NotificationBaseTestCase):

    def test_basic_creation(self):
        n = self.make_notification()
        self.assertIsNotNone(n.pk)

    def test_default_status_is_pending(self):
        n = Notification.objects.create(
            notification_type=Notification.Type.GENERAL,
            recipient_email="d@example.com",
            subject="S",
        )
        self.assertEqual(n.status, Notification.Status.PENDING)

    def test_default_notification_type_is_general(self):
        n = Notification.objects.create(
            recipient_email="d2@example.com",
            subject="S",
        )
        self.assertEqual(n.notification_type, Notification.Type.GENERAL)

    def test_default_retry_count_is_zero(self):
        n = self.make_notification()
        self.assertEqual(n.retry_count, 0)

    def test_default_metadata_is_empty_dict(self):
        n = self.make_notification()
        self.assertEqual(n.metadata, {})

    def test_metadata_stores_arbitrary_data(self):
        n = self.make_notification(metadata={"user_id": 42, "extra": "info"})
        n.refresh_from_db()
        self.assertEqual(n.metadata["user_id"], 42)

    def test_content_html_can_be_blank(self):
        n = self.make_notification(content_html="")
        self.assertEqual(n.content_html, "")

    def test_content_text_can_be_blank(self):
        n = self.make_notification(content_text="")
        self.assertEqual(n.content_text, "")

    def test_last_error_is_nullable(self):
        n = self.make_notification()
        self.assertIsNone(n.last_error)

    def test_sent_at_is_nullable(self):
        n = self.make_notification()
        self.assertIsNone(n.sent_at)

    def test_idempotency_key_can_be_null(self):
        n = self.make_notification(idempotency_key=None)
        self.assertIsNone(n.idempotency_key)

    def test_idempotency_key_unique(self):
        self.make_notification(idempotency_key="unique-abc")
        with self.assertRaises(IntegrityError):
            self.make_notification(idempotency_key="unique-abc")

    def test_multiple_null_idempotency_keys_allowed(self):
        """NULL is not considered equal to NULL in unique constraints."""
        self.make_notification(idempotency_key=None)
        self.make_notification(idempotency_key=None)
        self.assertEqual(
            Notification.objects.filter(idempotency_key__isnull=True).count(), 2
        )

    def test_created_at_auto_set(self):
        n = self.make_notification()
        self.assertIsNotNone(n.created_at)

    def test_updated_at_auto_set(self):
        n = self.make_notification()
        self.assertIsNotNone(n.updated_at)


class NotificationTypeTests(NotificationBaseTestCase):

    def _make(self, ntype):
        return self.make_notification(notification_type=ntype)

    def test_type_signup(self):
        n = self._make(Notification.Type.SIGNUP)
        self.assertEqual(n.notification_type, "SIGNUP")

    def test_type_contact(self):
        n = self._make(Notification.Type.CONTACT)
        self.assertEqual(n.notification_type, "CONTACT")

    def test_type_resource_upload(self):
        n = self._make(Notification.Type.RESOURCE_UPLOAD)
        self.assertEqual(n.notification_type, "RESOURCE_UPLOAD")

    def test_type_security_alert(self):
        n = self._make(Notification.Type.SECURITY_ALERT)
        self.assertEqual(n.notification_type, "SECURITY_ALERT")

    def test_type_general(self):
        n = self._make(Notification.Type.GENERAL)
        self.assertEqual(n.notification_type, "GENERAL")

    def test_type_generic_message(self):
        n = self._make(Notification.Type.GENERIC_MESSAGE)
        self.assertEqual(n.notification_type, "GENERIC_MESSAGE")


class NotificationStatusTests(NotificationBaseTestCase):

    def test_status_pending(self):
        n = self.make_notification(status=Notification.Status.PENDING)
        self.assertEqual(n.status, "PENDING")

    def test_status_sent(self):
        n = self.make_notification(status=Notification.Status.SENT)
        self.assertEqual(n.status, "SENT")

    def test_status_failed(self):
        n = self.make_notification(status=Notification.Status.FAILED)
        self.assertEqual(n.status, "FAILED")

    def test_status_retrying(self):
        n = self.make_notification(status=Notification.Status.RETRYING)
        self.assertEqual(n.status, "RETRYING")

    def test_status_update(self):
        n = self.make_notification(status=Notification.Status.PENDING)
        n.status = Notification.Status.SENT
        n.sent_at = timezone.now()
        n.save(update_fields=["status", "sent_at"])
        n.refresh_from_db()
        self.assertEqual(n.status, Notification.Status.SENT)
        self.assertIsNotNone(n.sent_at)


class NotificationStrTests(NotificationBaseTestCase):

    def test_str_contains_status(self):
        n = self.make_notification(status=Notification.Status.PENDING)
        self.assertIn("Pending", str(n))

    def test_str_contains_type(self):
        n = self.make_notification(notification_type=Notification.Type.SIGNUP)
        self.assertIn("SIGNUP", str(n))

    def test_str_contains_recipient(self):
        n = self.make_notification(recipient_email="check@example.com")
        self.assertIn("check@example.com", str(n))


class NotificationOrderingTests(NotificationBaseTestCase):

    def test_ordering_newest_first(self):
        n1 = self.make_notification(subject="First")
        n2 = self.make_notification(subject="Second")
        notifications = list(Notification.objects.all())
        self.assertEqual(notifications[0].pk, n2.pk)
        self.assertEqual(notifications[1].pk, n1.pk)
