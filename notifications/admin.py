from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Notification
from .tasks import send_notification_task

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'notification_type', 
        'recipient_email', 
        'status_pill', 
        'retry_count', 
        'created_at', 
        'sent_at'
    )
    list_filter = ('status', 'notification_type', 'created_at')
    search_fields = ('recipient_email', 'subject', 'content_text', 'idempotency_key')
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'idempotency_key', 'retry_count', 'last_error')
    actions = ['retry_notification']

    def status_pill(self, obj):
        colors = {
            Notification.Status.PENDING: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
            Notification.Status.SENT: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
            Notification.Status.FAILED: 'bg-red-500/10 text-red-500 border-red-500/20',
            Notification.Status.RETRYING: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
        }
        color_class = colors.get(obj.status, 'bg-gray-500/10 text-gray-500 border-gray-500/20')
        return format_html(
            '<span class="px-2.5 py-1 rounded-lg border text-[10px] font-bold uppercase tracking-wider {}">{}</span>',
            color_class,
            obj.get_status_display()
        )
    status_pill.short_description = _('Status')

    @admin.action(description=_("Retry sending selected notifications"))
    def retry_notification(self, request, queryset):
        count = 0
        for notification in queryset:
            if notification.status != Notification.Status.SENT:
                notification.status = Notification.Status.PENDING
                notification.save(update_fields=['status'])
                send_notification_task.delay(notification.id)
                count += 1
        self.message_user(request, f"Queued {count} notifications for retry.")
