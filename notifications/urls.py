from django.urls import path

from notifications import admin_views

urlpatterns = [
    # Notifications
    path("", admin_views.AdminNotificationListView.as_view(), name="notification_list"),
    path("notifications/<int:pk>/retry/", admin_views.AdminNotificationRetryView.as_view(), name="notification_retry"),
    path("notifications/<int:pk>/delete/", admin_views.AdminNotificationDeleteView.as_view(), name="notification_delete"),
]
