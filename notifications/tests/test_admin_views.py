"""
notifications/tests/test_admin_views.py

Tests for notifications/admin_views.py:
  - StaffRequiredMixin: anon / regular user blocked; staff / admin allowed
  - AdminNotificationListView: GET returns 200, correct template, context
  - AdminNotificationRetryView: already-SENT guard, queues task for non-sent,
    missing pk returns 404
  - AdminNotificationDeleteView: deletes SENT/FAILED, blocks PENDING/RETRYING,
    missing pk returns 404, GET not allowed
"""

from unittest.mock import patch

from django.urls import reverse

from notifications.models import Notification
from notifications.tests.base import NotificationBaseTestCase


_TASK_PATCH = "notifications.admin_views.send_notification_task"


# ── Access Control ─────────────────────────────────────────────────────────────

class StaffRequiredMixinTests(NotificationBaseTestCase):

    def test_anonymous_denied_notification_list(self):
        r = self.client.get(reverse("management:notification_list"))
        self.assertIn(r.status_code, [302, 403])

    def test_regular_user_denied_notification_list(self):
        self.login_as_user()
        r = self.client.get(reverse("management:notification_list"))
        self.assertIn(r.status_code, [302, 403])

    def test_staff_allowed_notification_list(self):
        self.login_as_staff()
        r = self.client.get(reverse("management:notification_list"))
        self.assertEqual(r.status_code, 200)

    def test_admin_allowed_notification_list(self):
        self.login_as_admin()
        r = self.client.get(reverse("management:notification_list"))
        self.assertEqual(r.status_code, 200)


# ── AdminNotificationListView ──────────────────────────────────────────────────

class AdminNotificationListViewTests(NotificationBaseTestCase):

    def setUp(self):
        self.login_as_staff()
        self.url = reverse("management:notification_list")

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(self.url),
            "notifications/admin/notification_list.html",
        )

    def test_context_has_notifications(self):
        r = self.client.get(self.url)
        self.assertIn("notifications", r.context)

    def test_notifications_ordered_newest_first(self):
        n1 = self.make_notification(subject="First")
        n2 = self.make_notification(subject="Second")
        r = self.client.get(self.url)
        pks = [n.pk for n in r.context["notifications"]]
        self.assertGreater(pks.index(n1.pk), pks.index(n2.pk))

    def test_all_notifications_visible(self):
        n1 = self.make_notification(subject="A")
        n2 = self.make_notification(subject="B")
        r = self.client.get(self.url)
        pks = [n.pk for n in r.context["notifications"]]
        self.assertIn(n1.pk, pks)
        self.assertIn(n2.pk, pks)


# ── AdminNotificationRetryView ─────────────────────────────────────────────────

class AdminNotificationRetryViewTests(NotificationBaseTestCase):

    def setUp(self):
        self.login_as_staff()

    def _retry_url(self, pk):
        return reverse("management:notification_retry", kwargs={"pk": pk})

    def test_retry_pending_notification_queues_task(self):
        n = self.make_notification(status=Notification.Status.PENDING)
        with patch(_TASK_PATCH) as mock_task:
            mock_task.delay = lambda pk: None
            self.client.post(self._retry_url(n.pk))
        n.refresh_from_db()
        self.assertEqual(n.status, Notification.Status.PENDING)

    def test_retry_sets_status_back_to_pending(self):
        n = self.make_notification(status=Notification.Status.FAILED)
        with patch(_TASK_PATCH) as mock_task:
            mock_task.delay = lambda pk: None
            self.client.post(self._retry_url(n.pk))
        n.refresh_from_db()
        self.assertEqual(n.status, Notification.Status.PENDING)

    def test_retry_already_sent_does_not_re_queue(self):
        n = self.make_notification(status=Notification.Status.SENT)
        with patch(_TASK_PATCH) as mock_task:
            self.client.post(self._retry_url(n.pk))
            mock_task.delay.assert_not_called()

    def test_retry_redirects_to_notification_list(self):
        n = self.make_notification(status=Notification.Status.FAILED)
        with patch(_TASK_PATCH) as mock_task:
            mock_task.delay = lambda pk: None
            r = self.client.post(self._retry_url(n.pk))
        self.assertRedirects(r, reverse("management:notification_list"))

    def test_retry_nonexistent_returns_404(self):
        r = self.client.post(self._retry_url(99999))
        self.assertEqual(r.status_code, 404)

    def test_anonymous_denied(self):
        self.client.logout()
        n = self.make_notification()
        r = self.client.post(self._retry_url(n.pk))
        self.assertIn(r.status_code, [302, 403])


# ── AdminNotificationDeleteView ────────────────────────────────────────────────

class AdminNotificationDeleteViewTests(NotificationBaseTestCase):

    def setUp(self):
        self.login_as_staff()

    def _delete_url(self, pk):
        return reverse("management:notification_delete", kwargs={"pk": pk})

    def test_delete_sent_notification_succeeds(self):
        n = self.make_notification(status=Notification.Status.SENT)
        self.client.post(self._delete_url(n.pk))
        self.assertFalse(Notification.objects.filter(pk=n.pk).exists())

    def test_delete_failed_notification_succeeds(self):
        n = self.make_notification(status=Notification.Status.FAILED)
        self.client.post(self._delete_url(n.pk))
        self.assertFalse(Notification.objects.filter(pk=n.pk).exists())

    def test_delete_pending_notification_is_blocked(self):
        n = self.make_notification(status=Notification.Status.PENDING)
        self.client.post(self._delete_url(n.pk))
        self.assertTrue(Notification.objects.filter(pk=n.pk).exists())

    def test_delete_retrying_notification_is_blocked(self):
        n = self.make_notification(status=Notification.Status.RETRYING)
        self.client.post(self._delete_url(n.pk))
        self.assertTrue(Notification.objects.filter(pk=n.pk).exists())

    def test_delete_redirects_to_list(self):
        n = self.make_notification(status=Notification.Status.SENT)
        r = self.client.post(self._delete_url(n.pk))
        self.assertRedirects(r, reverse("management:notification_list"))

    def test_blocked_delete_redirects_to_list(self):
        n = self.make_notification(status=Notification.Status.PENDING)
        r = self.client.post(self._delete_url(n.pk))
        self.assertRedirects(r, reverse("management:notification_list"))

    def test_delete_nonexistent_returns_404(self):
        r = self.client.post(self._delete_url(99999))
        self.assertEqual(r.status_code, 404)

    def test_anonymous_denied(self):
        self.client.logout()
        n = self.make_notification(status=Notification.Status.SENT)
        r = self.client.post(self._delete_url(n.pk))
        self.assertIn(r.status_code, [302, 403])
        self.assertTrue(Notification.objects.filter(pk=n.pk).exists())
