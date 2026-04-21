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
