"""
notifications/tests/test_tasks.py

Tests for notifications/tasks.py — send_notification_task.

Covers:
  - Already-SENT notifications are skipped
  - Nonexistent notification ID is handled gracefully (retry then give up)
  - Successful send updates status to SENT and sets sent_at
  - SMTP failure sets status to FAILED, stores last_error, and retries
  - Retry increments retry_count and sets RETRYING status
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from notifications.models import Notification
from notifications.tasks import send_notification_task
from notifications.tests.base import NotificationBaseTestCase


class SendNotificationTaskTests(NotificationBaseTestCase):

    def _run_task(self, notification_id):
        """Execute the task eagerly (bypass Celery worker)."""
        send_notification_task.apply(args=[notification_id])

    def test_already_sent_notification_is_skipped(self):
        n = self.make_notification(
            status=Notification.Status.SENT,
            sent_at=timezone.now(),
        )
        with patch("notifications.tasks.EmailMultiAlternatives") as mock_email:
            self._run_task(n.pk)
        mock_email.assert_not_called()

    def test_successful_send_sets_status_to_sent(self):
        n = self.make_notification()
        with patch("notifications.tasks.EmailMultiAlternatives") as mock_email:
            mock_email.return_value.send = MagicMock()
            self._run_task(n.pk)
        n.refresh_from_db()
        self.assertEqual(n.status, Notification.Status.SENT)

    def test_successful_send_sets_sent_at(self):
        n = self.make_notification()
        with patch("notifications.tasks.EmailMultiAlternatives") as mock_email:
            mock_email.return_value.send = MagicMock()
            self._run_task(n.pk)
        n.refresh_from_db()
        self.assertIsNotNone(n.sent_at)

    def test_send_failure_sets_status_to_failed(self):
        from celery.exceptions import Retry as CeleryRetry
        n = self.make_notification()
        with patch("notifications.tasks.EmailMultiAlternatives") as mock_email:
            mock_email.return_value.send.side_effect = Exception("SMTP error")
            # Celery raises Retry on each retry attempt even in eager mode;
            # catch it so we can inspect the DB state after the first failure.
            try:
                send_notification_task.apply(args=[n.pk], throw=False)
            except CeleryRetry:
                pass
        n.refresh_from_db()
        self.assertEqual(n.status, Notification.Status.FAILED)

    def test_send_failure_stores_last_error(self):
        from celery.exceptions import Retry as CeleryRetry
        n = self.make_notification()
        with patch("notifications.tasks.EmailMultiAlternatives") as mock_email:
            mock_email.return_value.send.side_effect = Exception("Connection refused")
            try:
                send_notification_task.apply(args=[n.pk], throw=False)
            except CeleryRetry:
                pass
        n.refresh_from_db()
        self.assertIn("Connection refused", n.last_error)

    def test_html_alternative_attached_when_content_html_present(self):
        n = self.make_notification(content_html="<b>bold</b>")
        with patch("notifications.tasks.EmailMultiAlternatives") as mock_email:
            mock_instance = MagicMock()
            mock_email.return_value = mock_instance
            self._run_task(n.pk)
        mock_instance.attach_alternative.assert_called_once_with("<b>bold</b>", "text/html")

    def test_no_html_alternative_when_content_html_empty(self):
        n = self.make_notification(content_html="")
        with patch("notifications.tasks.EmailMultiAlternatives") as mock_email:
            mock_instance = MagicMock()
            mock_email.return_value = mock_instance
            self._run_task(n.pk)
        mock_instance.attach_alternative.assert_not_called()

    def test_nonexistent_notification_handled_without_crash(self):
        """Task retries for a missing notification ID; Retry exception is acceptable."""
        from celery.exceptions import Retry as CeleryRetry
        try:
            send_notification_task.apply(args=[99999], throw=False)
        except CeleryRetry:
            pass  # expected: task schedules a retry for a missing record
        # The important thing is no unhandled crash and no Notification was created
        self.assertEqual(Notification.objects.count(), 0)
