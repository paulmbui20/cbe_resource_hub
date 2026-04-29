from notifications.tests.test_models import (
    NotificationCreationTests,
    NotificationTypeTests,
    NotificationStatusTests,
    NotificationStrTests,
    NotificationOrderingTests,
)
from notifications.tests.test_notifier import (
    GetAdminsTests,
    SendTemplateEmailTests,
    NotifyFunctionsTests,
)
from notifications.tests.test_tasks import SendNotificationTaskTests
from notifications.tests.test_admin_views import (
    StaffRequiredMixinTests,
    AdminNotificationListViewTests,
    AdminNotificationRetryViewTests,
    AdminNotificationDeleteViewTests,
)

__all__ = [
    # Models
    "NotificationCreationTests",
    "NotificationTypeTests",
    "NotificationStatusTests",
    "NotificationStrTests",
    "NotificationOrderingTests",
    # Notifier
    "GetAdminsTests",
    "SendTemplateEmailTests",
    "NotifyFunctionsTests",
    # Tasks
    "SendNotificationTaskTests",
    # Admin views
    "StaffRequiredMixinTests",
    "AdminNotificationListViewTests",
    "AdminNotificationRetryViewTests",
    "AdminNotificationDeleteViewTests",
]
