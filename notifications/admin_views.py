from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from .models import Notification
from .tasks import send_notification_task


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class AdminNotificationListView(StaffRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/admin/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 50

    def get_queryset(self) -> QuerySet:
        return Notification.objects.all().order_by("-created_at")


class AdminNotificationRetryView(StaffRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)

        if notification.status == Notification.Status.SENT:
            messages.info(request, "This notification was already sent successfully.")
        else:
            notification.status = Notification.Status.PENDING
            notification.save(update_fields=['status'])
            send_notification_task.delay(notification.id)
            messages.success(request, f"Notification #{notification.id} has been queued for retry.")

        return redirect("management:notification_list")


class AdminNotificationDeleteView(StaffRequiredMixin, View):
    """
    Deletes a notification record. Only SENT or FAILED notifications may be deleted.
    PENDING and RETRYING records are protected to avoid orphaned Celery tasks.
    """
    DELETABLE_STATUSES = {Notification.Status.SENT, Notification.Status.FAILED}

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)

        if notification.status not in self.DELETABLE_STATUSES:
            messages.error(
                request,
                f"Notification #{notification.id} cannot be deleted while it is "
                f"'{notification.get_status_display()}'. Only Sent or Failed notifications may be deleted."
            )
            return redirect("management:notification_list")

        notification.delete()
        messages.success(request, f"Notification #{pk} deleted successfully.")
        return redirect("management:notification_list")
