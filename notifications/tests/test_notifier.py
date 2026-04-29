"""
notifications/tests/test_notifier.py

Tests for notifications/notifier.py:
  - _send_template_email: creates record, respects idempotency key,
    returns None on duplicate, queues task via on_commit
  - notify_signup, notify_contact_form, notify_lockout,
    notify_resource_upload, notify_generic_message:
    each creates one record per admin, skips duplicates
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from notifications.models import Notification
from notifications.notifier import (
    _get_admins,
    _send_template_email,
    notify_contact_form,
    notify_generic_message,
    notify_lockout,
    notify_resource_upload,
    notify_signup,
)

ADMIN_EMAIL = "admin@example.com"
ADMIN_SETTINGS = [("Admin", ADMIN_EMAIL)]

# Patch template rendering so we don't need real template files in tests
_RENDER_PATCH = "notifications.notifier.render_to_string"
_TASK_PATCH = "notifications.notifier.send_notification_task"


def _fake_render(template, context):
    return f"<rendered:{template}>"


@override_settings(ADMINS=ADMIN_SETTINGS)
class GetAdminsTests(TestCase):

    def test_returns_list_of_emails(self):
        admins = _get_admins()
        self.assertIn(ADMIN_EMAIL, admins)

    def test_returns_empty_list_when_no_admins(self):
        with self.settings(ADMINS=[]):
            admins = _get_admins()
            self.assertEqual(admins, [])


@override_settings(ADMINS=ADMIN_SETTINGS)
class SendTemplateEmailTests(TestCase):

    def setUp(self):
        self.render_patcher = patch(_RENDER_PATCH, side_effect=_fake_render)
        self.task_patcher = patch(_TASK_PATCH)
        self.mock_render = self.render_patcher.start()
        self.mock_task = self.task_patcher.start()
        self.mock_task.delay = MagicMock()

    def tearDown(self):
        self.render_patcher.stop()
        self.task_patcher.stop()

    def _send(self, key=None):
        return _send_template_email(
            recipient="r@example.com",
            subject="Test",
            template_name="signup_admin",
            context={"user": MagicMock(id=1, email="u@example.com")},
            notification_type=Notification.Type.SIGNUP,
            idempotency_key=key,
        )

    def test_creates_notification_record(self):
        n = self._send(key="k1")
        self.assertIsNotNone(n)
        self.assertTrue(Notification.objects.filter(pk=n.pk).exists())

    def test_returns_notification_instance(self):
        n = self._send(key="k2")
        self.assertIsInstance(n, Notification)

    def test_notification_has_correct_type(self):
        n = self._send(key="k3")
        self.assertEqual(n.notification_type, Notification.Type.SIGNUP)

    def test_notification_has_correct_recipient(self):
        n = self._send(key="k4")
        self.assertEqual(n.recipient_email, "r@example.com")

    def test_notification_default_status_is_pending(self):
        n = self._send(key="k5")
        self.assertEqual(n.status, Notification.Status.PENDING)

    def test_idempotency_returns_none_on_duplicate(self):
        self._send(key="dup-key")
        result = self._send(key="dup-key")
        self.assertIsNone(result)

    def test_idempotency_does_not_create_duplicate(self):
        self._send(key="dup-key2")
        self._send(key="dup-key2")
        self.assertEqual(Notification.objects.filter(idempotency_key="dup-key2").count(), 1)

    def test_no_idempotency_key_always_creates(self):
        self._send(key=None)
        self._send(key=None)
        self.assertEqual(Notification.objects.count(), 2)

    def test_current_year_injected_into_context(self):
        from django.utils import timezone
        self._send(key="year-k")
        # render_to_string was called; check the context arg had current_year
        call_args = self.mock_render.call_args_list[0]
        context_arg = call_args[0][1]
        self.assertIn("current_year", context_arg)
        self.assertEqual(context_arg["current_year"], timezone.now().year)

    def test_metadata_stored_from_context(self):
        with patch(_RENDER_PATCH, side_effect=_fake_render):
            n = _send_template_email(
                recipient="r@example.com",
                subject="Meta",
                template_name="signup_admin",
                context={"metadata": {"foo": "bar"}},
                notification_type=Notification.Type.GENERAL,
                idempotency_key="meta-key",
            )
        self.assertEqual(n.metadata, {"foo": "bar"})


@override_settings(ADMINS=ADMIN_SETTINGS)
class NotifyFunctionsTests(TestCase):
    """Test each public notify_* function creates exactly one record per admin."""

    def setUp(self):
        self.render_patcher = patch(_RENDER_PATCH, side_effect=_fake_render)
        self.task_patcher = patch(_TASK_PATCH)
        self.render_patcher.start()
        mock_task = self.task_patcher.start()
        mock_task.delay = MagicMock()

    def tearDown(self):
        self.render_patcher.stop()
        self.task_patcher.stop()

    def test_notify_signup_creates_record(self):
        user = MagicMock(id=99, email="new@example.com")
        notify_signup(user)
        self.assertEqual(Notification.objects.filter(
            notification_type=Notification.Type.SIGNUP
        ).count(), 1)

    def test_notify_signup_idempotent(self):
        user = MagicMock(id=100, email="idem@example.com")
        notify_signup(user)
        notify_signup(user)
        self.assertEqual(Notification.objects.filter(
            notification_type=Notification.Type.SIGNUP
        ).count(), 1)

    def test_notify_contact_form_creates_record(self):
        msg = MagicMock(id=1, subject="Hello")
        notify_contact_form(msg)
        self.assertEqual(Notification.objects.filter(
            notification_type=Notification.Type.CONTACT
        ).count(), 1)

    def test_notify_contact_form_idempotent(self):
        msg = MagicMock(id=2, subject="Hello again")
        notify_contact_form(msg)
        notify_contact_form(msg)
        self.assertEqual(Notification.objects.filter(
            notification_type=Notification.Type.CONTACT
        ).count(), 1)

    def test_notify_lockout_creates_record(self):
        notify_lockout("1.2.3.4", "attacker", "badbot/1.0")
        self.assertEqual(Notification.objects.filter(
            notification_type=Notification.Type.SECURITY_ALERT
        ).count(), 1)

    def test_notify_resource_upload_creates_record(self):
        resource = MagicMock(id=10, title="My Resource")
        notify_resource_upload(resource)
        self.assertEqual(Notification.objects.filter(
            notification_type=Notification.Type.RESOURCE_UPLOAD
        ).count(), 1)

    def test_notify_resource_upload_idempotent(self):
        resource = MagicMock(id=11, title="My Resource 2")
        notify_resource_upload(resource)
        notify_resource_upload(resource)
        self.assertEqual(Notification.objects.filter(
            notification_type=Notification.Type.RESOURCE_UPLOAD
        ).count(), 1)

    def test_notify_generic_message_creates_record(self):
        notify_generic_message("Subject", "Body message", {"ctx": "data"})
        self.assertEqual(Notification.objects.filter(
            notification_type=Notification.Type.GENERIC_MESSAGE
        ).count(), 1)

    @override_settings(ADMINS=[])
    def test_no_admins_creates_no_records(self):
        user = MagicMock(id=200, email="ghost@example.com")
        notify_signup(user)
        self.assertEqual(Notification.objects.count(), 0)
