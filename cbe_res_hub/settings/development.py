"""
development.py — local development settings.

Inherits everything from base and applies:
  - Local filesystem storage (overrides R2)
  - Optional debug-toolbar and silk profiler (env-gated)
  - Optional SQLite fallback (USE_SQLITE=True)
  - Browser-cache-busting middleware
  - Elevated log level when DEBUG=True

"""
from urllib.parse import urlparse, parse_qsl

from .base import *  # noqa: F401, F403
from .base import (
    DEFAULT_APPS,
    LOGGING,
    MAIN_MIDDLEWARE,
    MY_APPS,
    THIRD_PARTY_APPS,
    BASE_DIR,
    DEBUG,
    _cf_settings,
)

# ── Local filesystem storage ──────────────────────────────────────────────────
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "protected": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "public_files": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "dbbackup": {
        "BACKEND": "helpers.cloudflare.storages.DbBackupPrivateStorage",
        "OPTIONS": _cf_settings.CLOUDFLARE_R2_BACKUP_CONFIG_OPTIONS,
    },
}

# ── Optional tools (debug_toolbar, silk) ─────────────────────────────────────
LOCAL_APPS: list[str] = []
LOCAL_MIDDLEWARE: list[str] = []

enable_debug_toolbar = os.getenv("ENABLE_DEBUG_TOOLBAR", "True")
ENABLE_DEBUG_TOOLBAR = ast.literal_eval(enable_debug_toolbar) if enable_debug_toolbar and DEBUG else False

if ENABLE_DEBUG_TOOLBAR:
    LOCAL_APPS.append("debug_toolbar")
    LOCAL_MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

enable_silk = os.getenv("ENABLE_SILK", "False")
ENABLE_SILK = ast.literal_eval(enable_silk) if enable_silk and DEBUG else False

if ENABLE_SILK:
    LOCAL_APPS.append("silk")
    LOCAL_MIDDLEWARE.append("silk.middleware.SilkyMiddleware")
    SILKY_PYTHON_PROFILER = True

INSTALLED_APPS: list[str] = DEFAULT_APPS + THIRD_PARTY_APPS + MY_APPS + LOCAL_APPS

# Disable browser caching so you always see fresh responses locally
_dev_middleware = list(MAIN_MIDDLEWARE)
_dev_middleware.insert(0, "cbe_res_hub.middleware.DisableBrowserCacheMiddleware")
MIDDLEWARE: list[str] = _dev_middleware + LOCAL_MIDDLEWARE

# ── Optional SQLite fallback ──────────────────────────────────────────────────
use_sqlite_env_var = os.getenv("USE_SQLITE", "False")
USE_SQLITE = ast.literal_eval(use_sqlite_env_var) if use_sqlite_env_var else False
if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # ──────────────────────────────────────────────────────────────────────────────
    # DATABASE  (PostgreSQL via DATABASE_URL_LOCAL)
    # ──────────────────────────────────────────────────────────────────────────────
    _db_url = urlparse(
        require_env("DATABASE_URL_LOCAL")
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

# ── Logging ───────────────────────────────────────────────────────────────────
if DEBUG:
    LOGGING["loggers"][""]["level"] = "DEBUG"
