"""
production.py — production environment settings.

Inherits everything from base and applies:
  - Security hardening (HTTPS cookies, proxy headers, HSTS)
  - Cloudflare R2 dual-bucket storage
  - Page-level cache middleware
  - JSON logging (dev_console handler removed)

"""
import os
from urllib.parse import urlparse, parse_qsl

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401, F403
from .base import (
    LOGGING,
    MAIN_MIDDLEWARE,
    _cf_settings,
    _private_r2,
    _public_r2,
    _backup_r2,
    require_env,
    environment,
)

# ──────────────────────────────────────────────────────────────────────────────
# DATABASE  (PostgreSQL via DATABASE_URL)
# ──────────────────────────────────────────────────────────────────────────────
_db_url = urlparse(
    require_env("DATABASE_URL")
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _db_url.path.lstrip("/"),
        "USER": _db_url.username,
        "PASSWORD": _db_url.password,
        "HOST": _db_url.hostname,
        "PORT": _db_url.port,
        "OPTIONS": {
            **dict(parse_qsl(_db_url.query)),
            "connect_timeout": 5,
            "options": "-c search_path=public",
        },
        "CONN_MAX_AGE": 600,
    }
}

# ── Security hardening ────────────────────────────────────────────────────────
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 1_209_600  # 2 weeks
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
DEBUG = False

# ── Logging: strip dev_console from every logger ──────────────────────────────
for _logger_cfg in LOGGING["loggers"].values():
    if "dev_console" in _logger_cfg.get("handlers", []):
        _logger_cfg["handlers"].remove("dev_console")

# ── Middleware: add page-level caching ────────────────────────────────────────
MIDDLEWARE = list(MAIN_MIDDLEWARE)
MIDDLEWARE.insert(1, "django.middleware.cache.UpdateCacheMiddleware")
MIDDLEWARE.append("django.middleware.cache.FetchFromCacheMiddleware")

# ── Storage: Cloudflare R2 dual-bucket ───────────────────────────────────────
if _private_r2 and _public_r2 and _backup_r2:
    STORAGES = {
        # Private media / resource file uploads  (signed URLs, 1-hour TTL)
        "default": {
            "BACKEND": "helpers.cloudflare.storages.MediaFileStorage",
            "OPTIONS": _cf_settings.CLOUDFLARE_R2_CONFIG_OPTIONS,
        },
        # Static files (CSS, JS) served from public CDN bucket
        "staticfiles": {
            "BACKEND": "helpers.cloudflare.storages.StaticFileStorage",
            "OPTIONS": _cf_settings.CLOUDFLARE_R2_PUBLIC_CONFIG_OPTIONS,
        },
        # Protected uploads (admin-only docs) — private bucket, /protected/ prefix
        "protected": {
            "BACKEND": "helpers.cloudflare.storages.ProtectedMediaStorage",
            "OPTIONS": _cf_settings.CLOUDFLARE_R2_CONFIG_OPTIONS,
        },
        # Publicly readable files (thumbnails, open resources) — public bucket
        "public_files": {
            "BACKEND": "helpers.cloudflare.storages.PublicFilesStorage",
            "OPTIONS": _cf_settings.CLOUDFLARE_R2_PUBLIC_CONFIG_OPTIONS,
        },
        # Database backups — dedicated isolated bucket
        "dbbackup": {
            "BACKEND": "helpers.cloudflare.storages.DbBackupPrivateStorage",
            "OPTIONS": _cf_settings.CLOUDFLARE_R2_BACKUP_CONFIG_OPTIONS,
        },
    }

# ──────────────────────────────────────────────────────────────────────────────
# DATABASE BACKUPS
# ──────────────────────────────────────────────────────────────────────────────
DBBACKUP_CLEANUP_KEEP: int = 14
DBBACKUP_CLEANUP_KEEP_MEDIA: int = 0
DBBACKUP_CONNECTORS = {
    "default": {"CONNECTOR": "dbbackup.db.postgresql.PgDumpConnector"}
}
DBBACKUP_FILENAME_TEMPLATE = "{databasename}-{datetime}.{extension}"
DBBACKUP_DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"
DBBACKUP_DATABASES = ["default"]

# ──────────────────────────────────────────────────────────────────────────────
# SENTRY
# ──────────────────────────────────────────────────────────────────────────────

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=True,
        environment=environment,
    )
