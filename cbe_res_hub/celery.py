"""
Celery configuration for CBE Resources Hub project.

Design goals:
- Prevent task pile-ups after restart

Key principles used:
- Expiration on time-sensitive tasks
- Load staggering to reduce DB and CPU spikes
"""

import os
from celery import Celery
from celery.schedules import crontab

# ------------------------------------------------------------------------------
# Django settings
# ------------------------------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbe_res_hub.settings")

app = Celery("cbe_res_hub")

# Load settings from Django with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py from installed apps
app.autodiscover_tasks()

# ------------------------------------------------------------------------------
# Time configuration
# ------------------------------------------------------------------------------
# Use local time to match business logic and ops expectations
app.conf.timezone = "Africa/Nairobi"
app.conf.enable_utc = False

# ------------------------------------------------------------------------------
# Celery Beat schedule
# ------------------------------------------------------------------------------
# IMPORTANT:
# - All nightly tasks have `expires` to avoid post-deploy pileups
# - Tasks are staggered to avoid DB contention
# ------------------------------------------------------------------------------

app.conf.beat_schedule = {

    "worker-health-check": {
        "task": "website.tasks.celery_worker_health_check",
        "schedule": crontab(minute=0, hour="*/2"),
        "options": {
            "expires": 300,
        },
    },

    "detailed-health-check-every-six-hours": {
        "task": "website.tasks.health_check_task",
        "schedule": crontab(minute=0, hour="*/6"),
        "options": {
            "expires": 900,
        },
    },

    "backup-health-check": {
        "task": "website.tasks.backup_health_check",
        "schedule": crontab(minute=0, hour="*/12"),
        "options": {
            "expires": 300,
        },
    },

    # ------------------------------------------------------------------
    # BACKUPS (I/O HEAVY – ISOLATED)
    # ------------------------------------------------------------------

    "daily-database-backup": {
        "task": "website.tasks.backup_database",
        "schedule": crontab(hour=0, minute=30), # at 12:30 am
        "kwargs": {"backup_type": "daily"},
        "options": {
            "expires": 3600,
        },
    },

    "weekly-full-backup": {
        "task": "website.tasks.backup_database",
        "schedule": crontab(hour=0, minute=45, day_of_week=0), # every sunday at 12:45 am
        "kwargs": {"backup_type": "weekly"},
        "options": {
            "expires": 3600,
        },
    },

    "cleanup-old-backups": {
        "task": "website.tasks.cleanup_old_backups",
        "schedule": crontab(hour=1, minute=15), # at 1:45 am daily
        "kwargs": {"keep_days": 14},
        "options": {
            "expires": 1800,
        },
    },
}
