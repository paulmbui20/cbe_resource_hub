# 📧 Notification System

A robust, asynchronous, and fault-tolerant system for handling all system-generated emails (signups, contact forms,
security alerts, and resource uploads).

## 🚀 Key Features

- **Asynchronous Delivery**: All emails are queued via Celery tasks to prevent blocking the request-response cycle.
- **Fault Tolerance**: Automatic exponential backoff retries (e.g., 1m, 2m, 4m...) for failed deliveries.
- **Idempotency**: Prevents sending duplicate emails for the same event using unique `idempotency_key` generation.
- **Delivery Monitoring**: Full history of sent, pending, and failed notifications available in the custom Management
  Panel.
- **Manual Retries**: Admins can manually trigger retries for failed notifications directly from the dashboard.
- **Rate Limiting**: Integrated `rate_limit="10/m"` to protect SMTP throughput and avoid being flagged as spam.

## 🛠 For Developers

Sending a notification is designed to be extremely simple. Use the `notifier.py` utility:

```python
from notifications import notifier

# 1. Notify of a new signup (sent to ADMINS)
notifier.notify_signup(user)

# 2. Notify of a contact form submission
notifier.notify_contact_form(contact_message_obj)

# 3. Notify of a security lockout
notifier.notify_lockout(ip_address, username, user_agent)

# 4. Notify of a new resource upload
notifier.notify_resource_upload(resource_item_obj)
```

## 📂 File Structure

- `models.py`: Defines the `Notification` model with status tracking.
- `notifier.py`: The public API (utility functions) for triggering notifications.
- `tasks.py`: Celery tasks for rendering templates and sending the actual mail.
- `signals.py`: Automatic event listeners (allauth signals, axes signals, post_save hooks).
- `templates/notifications/`: Branded HTML and plain-text email templates.

## 📋 Management Dashboard

Access the notification history via the **System > Notifications** section in the sidebar.

- **Search**: Filter by recipient, subject, or type.
- **Status Pills**: Quickly identify `SENT`, `FAILED`, or `RETRYING` messages.
- **Error Logs**: Click the info icon on failed messages to see the exact SMTP or logic error.
- **Bulk Action**: Select multiple messages and use "Retry sending" to re-queue them.
