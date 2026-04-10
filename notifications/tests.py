import pytest
from notifications.models import Notification
from notifications.notifier import _send_template_email

@pytest.mark.django_db
def test_notification_creation():
    """Verify that a notification record can be created with standard fields."""
    notif = Notification.objects.create(
        notification_type=Notification.Type.GENERAL,
        recipient_email="test@example.com",
        subject="Test Subject",
        content_text="Test content",
        status=Notification.Status.PENDING
    )
    assert notif.id is not None
    assert notif.status == 'PENDING'
    assert Notification.objects.count() == 1

@pytest.mark.django_db
def test_notifier_idempotency(settings):
    """Verify that the notifier respects idempotency keys."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    
    context = {'metadata': {'test': True}}
    
    # First send
    n1 = _send_template_email(
        recipient="test@example.com",
        subject="Subject",
        template_name="signup_admin",
        context=context,
        notification_type=Notification.Type.SIGNUP,
        idempotency_key="unique_key_123"
    )
    assert n1 is not None
    assert Notification.objects.count() == 1
    
    # Second send with same key
    n2 = _send_template_email(
        recipient="test@example.com",
        subject="Subject",
        template_name="signup_admin",
        context=context,
        notification_type=Notification.Type.SIGNUP,
        idempotency_key="unique_key_123"
    )
    assert n2 is None
    assert Notification.objects.count() == 1
