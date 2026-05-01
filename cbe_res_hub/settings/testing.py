"""
testing.py — settings used during ``pytest`` / ``manage.py test`` runs.

Inherits base, then:
  - Disables rate-limiting blocks
  - Runs Celery tasks synchronously (no broker needed)
  - Switches all storage to local filesystem
  - Strips optional middleware to keep the stack minimal
"""

from .base import *  # noqa: F401, F403
from .base import (
    BASE_DIR,
    DEFAULT_APPS,
    MY_APPS,
    THIRD_PARTY_APPS,
    WAGTAIL_APPS,
    MAIN_MIDDLEWARE,
)

DEBUG = False

# ── Default to SQLITE for testing ─────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ── Rate limiting: non-blocking in tests ─────────────────────────────────────
RATELIMIT_MIDDLEWARE = {
    "DEFAULT_RATE": "150/m",
    "SKIP_PATHS": ["/admin/", "/health/", "/static/", "/favicon.ico", "/media/"],
    "BLOCK": False,
    "KEY_FUNCTION": "django_smart_ratelimit.utils.get_ip_key",
}

# ── Celery: run tasks inline, no broker required ─────────────────────────────
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── App ordering consistent with original test override ──────────────────────
INSTALLED_APPS = DEFAULT_APPS + MY_APPS + THIRD_PARTY_APPS + WAGTAIL_APPS

# ── Minimal middleware stack ──────────────────────────────────────────────────
MIDDLEWARE = list(MAIN_MIDDLEWARE)

# ── Local filesystem storage (no external deps) ───────────────────────────────
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": "test-default"},
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        "OPTIONS": {"location": "test-static"},
    },
    "protected": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": "test-protected"},
    },
    "public_files": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": "test-public-files"},
    },
    "dbbackup": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": "test-database-backups"},
    },
}
