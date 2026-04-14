"""
Django settings for cbe_res_hub — Django 6.0+ currently on (6.0.3)

Sections:
    1.  Core / Security
    2.  Application Definition
    3.  Middleware
    4.  Templates
    5.  Database  (Postgres via DATABASE_URL)
    6.  Cache     (Redis)
    7.  Storage   (Cloudflare R2 prod | Local dev)
    8.  Static & Media
    9.  Authentication
   10.  Internationalisation
   11.  Email
   12.  Celery
   13.  Django Channels (ASGI)
   14.  Logging
   15.  django-axes  (brute-force protection)
   16.  Rate Limiting
   17.  Sentry
   18.  TinyMCE / Taggit
   19.  Database Backups (dbbackup)
   20.  Misc / Site Identity
   21.  Test overrides
"""
from __future__ import annotations

import ast
import logging
import os
import ssl
import sys
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

load_dotenv()

# ── Resolve environment first so everything below can reference it ────────────
environment: str = os.getenv("ENVIRONMENT")
_prod: bool = environment == "production"

# ──────────────────────────────────────────────────────────────────────────────
# 1. CORE / SECURITY
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY: str = os.getenv("SECRET_KEY")

debug_env = os.getenv("DEBUG", "False")
DEBUG: bool = ast.literal_eval(debug_env) if debug_env or _prod else False

allowed_hosts = os.getenv("ALLOWED_HOSTS")
ALLOWED_HOSTS: list[str] = [h.strip() for h in allowed_hosts.split(",") if h.strip()]

csrf_origins = os.getenv("CSRF_ORIGINS")
CSRF_TRUSTED_ORIGINS: list[str] = (
    [h.strip() for h in csrf_origins.split(",") if h.strip()]
    if csrf_origins
    else []
)

INTERNAL_IPS: list[str] = ["127.0.0.1"]

# ──────────────────────────────────────────────────────────────────────────────
# 2. APPLICATION DEFINITION
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_APPS: list[str] = [
    "daphne",  # ASGI server — must be FIRST for channels
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
]

THIRD_PARTY_APPS: list[str] = [
    # Auth / UI
    "allauth_ui",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    'slippers',
    # Content / Forms
    "tinymce",
    "taggit",
    "widget_tweaks",
    # Async / Task queue
    "django_celery_results",
    "django_celery_beat",
    # Storage
    "storages",
    # Security / Monitoring
    "axes",
    "django_smart_ratelimit",
    # DB backups
    "dbbackup",
]

LOCAL_APPS: list[str] = [
    # Silk profiler (dev)
    "silk",
    "debug_toolbar",
]

MY_APPS: list[str] = [
    "accounts.apps.AccountsConfig",
    "cms.apps.CmsConfig",
    "resources.apps.ResourcesConfig",
    "website.apps.WebsiteConfig",
    "files.apps.FilesConfig",
    "seo.apps.SeoConfig",
    "notifications.apps.NotificationsConfig",
]

INSTALLED_APPS: list[str] = DEFAULT_APPS + THIRD_PARTY_APPS + MY_APPS

# ──────────────────────────────────────────────────────────────────────────────
# 3. MIDDLEWARE
# ──────────────────────────────────────────────────────────────────────────────
MAIN_MIDDLEWARE: list[str] = [
    "django_smart_ratelimit.middleware.RateLimitMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "axes.middleware.AxesMiddleware",
    "cbe_res_hub.middleware.ForcePasswordChangeMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "seo.middleware.SlugRedirectMiddleware",
]

LOCAL_MIDDLEWARE: list[str] = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "silk.middleware.SilkyMiddleware",
]

ROOT_URLCONF = "cbe_res_hub.urls"
WSGI_APPLICATION = "cbe_res_hub.wsgi.application"

# ──────────────────────────────────────────────────────────────────────────────
# 4. TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "website/templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Injects site_settings + menus into every template
                "cms.context_processors.global_settings",
                # Injects partner_banners (show_as_banner=True) into every template
                "website.context_processors.partner_banners",
            ],
        },
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# 5. DATABASE  (PostgreSQL via DATABASE_URL)
# ──────────────────────────────────────────────────────────────────────────────
_db_url = urlparse(
    os.getenv("DATABASE_URL") if _prod else os.getenv("DATABASE_URL_LOCAL")
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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ──────────────────────────────────────────────────────────────────────────────
# 6. CACHE  (Redis)
# ──────────────────────────────────────────────────────────────────────────────
_redis_url: str = os.getenv("REDIS_URL")
_redis_password: str = os.getenv("REDIS_PASSWORD")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{_redis_url}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": _redis_password or None,
            "IGNORE_EXCEPTIONS": True,
            "CONNECTION_POOL_KWARGS": {
                "retry_on_timeout": True,
                "socket_connect_timeout": 30,
                "socket_timeout": 300,
                "max_connections": 100,
            },
        },
        "KEY_PREFIX": "cbe",
        "TIMEOUT": 60 * 60,  # 1 hour
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# ──────────────────────────────────────────────────────────────────────────────
# 7. STORAGE  (Cloudflare R2 — dual-bucket | Local filesystem — dev)
#
#  Two R2 buckets:
#    Private bucket  → resource files / user media  (signed URLs, 1 h TTL)
#    Public  bucket  → static files (CSS/JS)        (public-read, CDN-cached)
#    Backup  bucket  → database backups             (private, separate creds)
#
#  Storage classes live in helpers/cloudflare/storages.py so the backend
#  string in STORAGES stays clean.  Each class sets its own location, ACL,
#  and Cache-Control header via get_object_parameters().
#
#  Env vars (private bucket):
#    CLOUDFLARE_R2_BUCKET, CLOUDFLARE_R2_BUCKET_ENDPOINT,
#    CLOUDFLARE_R2_ACCESS_KEY, CLOUDFLARE_R2_SECRET_KEY
#
#  Env vars (public bucket):
#    CLOUDFLARE_R2_PUBLIC_BUCKET, CLOUDFLARE_R2_PUBLIC_BUCKET_ENDPOINT,
#    CLOUDFLARE_R2_PUBLIC_ACCESS_KEY, CLOUDFLARE_R2_PUBLIC_SECRET_KEY,
#    CLOUDFLARE_R2_PUBLIC_CUSTOM_DOMAIN  (optional — e.g. cdn.example.com)
# ──────────────────────────────────────────────────────────────────────────────
from helpers.cloudflare import settings as _cf_settings  # noqa: E402

_private_r2 = bool(_cf_settings.CLOUDFLARE_R2_CONFIG_OPTIONS)
_public_r2 = bool(_cf_settings.CLOUDFLARE_R2_PUBLIC_CONFIG_OPTIONS)

# ── Backup bucket (shared config, independent of private/public buckets) ──────
_BACKUP_R2_OPTIONS: dict = {
    "access_key": os.getenv("BACKUP_R2_ACCESS_KEY_ID"),
    "secret_key": os.getenv("BACKUP_R2_SECRET_ACCESS_KEY"),
    "bucket_name": os.getenv("BACKUP_R2_BUCKET_NAME"),
    "region_name": os.getenv("BACKUP_R2_REGION", "auto"),
    "endpoint_url": os.getenv("BACKUP_R2_ENDPOINT"),
    "default_acl": "private",
    "file_overwrite": False,
    "location": "database-backups",
}

# ──────────────────────────────────────────────────────────────────────────────
# 8. STATIC & MEDIA URLs / Paths
# ──────────────────────────────────────────────────────────────────────────────
STATIC_ROOT = BASE_DIR / "static"  # collectstatic target (local / CI)

STATICFILES_DIRS = [
    BASE_DIR / "website/static",  # Bun/Tailwind compiled output
    "seo/static",
]

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STATIC_URL = "static/"

MEDIA_ROOT = BASE_DIR / "media"  # local dev upload target

MEDIA_URL = "/media/"

# ──────────────────────────────────────────────────────────────────────────────
# 9. AUTHENTICATION
# ──────────────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.CustomUser"

# allauth handles login/logout — point Django's built-ins at allauth's views
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    # 1. Axes must come first to intercept locked-out accounts
    "axes.backends.AxesStandaloneBackend",
    # 2. Standard Django backend (admin login, management commands)
    "django.contrib.auth.backends.ModelBackend",
    # 3. allauth — handles email + social auth
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID: int = int(os.getenv("SITE_ID", "1"))

# ── django-allauth core ───────────────────────────────────────────────────────
# Email is the only login credential — username is internal / auto-generated.
ACCOUNT_LOGIN_METHODS = {"email"}  # email-only (no username field)
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"  # we still have the column, just autofilled

# Email verification strategy
# "mandatory" → user must click the link before logging in (recommended for prod)
# "optional"  → can log in immediately, verification banner shown
# "none"      → skip entirely (fine for dev / social-only flows)
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "optional")

LOGIN_ON_EMAIL_CONFIRMATION = True  # auto-login after clicking link
LOGIN_ON_PASSWORD_RESET = True  # auto-login after password reset
ACCOUNT_SESSION_REMEMBER = True  # persistent sessions by default

LOGOUT_ON_GET = True # Logout user immediately after they click/hit the logout endpoint

# Rate limits (per django-allauth v0.60+ format)
ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/5m/ip",
    "change_password": "3/m/user",
    "reset_password": "3/m/ip",
    "signup": "5/m/ip",
    "confirm_email": "3/m/user",
}

# ── Custom adapters ───────────────────────────────────────────────────────────
ACCOUNT_ADAPTER = "accounts.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "accounts.adapters.SocialAccountAdapter"

# ── allauth-UI theme ──────────────────────────────────────────────────────────
ALLAUTH_UI_THEME = "dark"

# ── Google OAuth ──────────────────────────────────────────────────────────────

GOOGLE_OAUTH_CLIENT_ID= os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "secret": GOOGLE_OAUTH_CLIENT_SECRET,
        },
        "SCOPE": ["profile", "email", "openid"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
        "FETCH_USERINFO": True,
        "EMAIL_AUTHENTICATION": True,  # match social email to local account
    }
}

# Auto-connect social accounts to existing local accounts with the same email
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_LOGIN_ON_GET = True  # allow GET-based OAuth callback

# ──────────────────────────────────────────────────────────────────────────────
# 10. INTERNATIONALISATION
# ──────────────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────────────────────────────────────
# 11. EMAIL
# ──────────────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST: str = os.getenv("EMAIL_HOST")
EMAIL_PORT: int = int(os.getenv("EMAIL_PORT"))
_email_tls = os.getenv("EMAIL_USE_TLS")
EMAIL_USE_TLS: bool = ast.literal_eval(_email_tls) if _email_tls else True
EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD: str = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL: str = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# ──────────────────────────────────────────────────────────────────────────────
# 12. CELERY
# ──────────────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL: str = f"{_redis_url}/2"
CELERY_RESULT_BACKEND: str = f"{_redis_url}/3"
CELERY_ACCEPT_CONTENT: list[str] = ["json"]
CELERY_TASK_SERIALIZER: str = "json"
CELERY_RESULT_SERIALIZER: str = "json"
CELERY_TIMEZONE: str = TIME_ZONE
CELERY_TASK_TRACK_STARTED: bool = True
CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutes soft limit

if _redis_url and _redis_url.startswith("rediss://"):
    _ssl_config = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
    CELERY_BROKER_USE_SSL = _ssl_config
    CELERY_REDIS_BACKEND_USE_SSL = _ssl_config

# ──────────────────────────────────────────────────────────────────────────────
# 13. DJANGO CHANNELS / ASGI
# ──────────────────────────────────────────────────────────────────────────────
ASGI_APPLICATION = "cbe_res_hub.asgi.application"

if _redis_url:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [
                    {
                        "address": _redis_url,
                        "password": _redis_password or None,
                    }
                ],
                "prefix": "cbe_asgi:",
                "channel_capacity": {
                    "http.request": 200,
                    "http.response!*": 100,
                    "websocket.send!*": 100,
                },
            },
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

# ──────────────────────────────────────────────────────────────────────────────
# 14. LOGGING
#     All output → stdout / stderr — no files, no RotatingFileHandler.
#     Production: "json" formatter | Development: "simple"
# ──────────────────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
        "skip_static_requests": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda record: not record.getMessage().startswith("GET /static/"),
        },
    },

    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname:8} {name:30} {module:15} {funcName:15} {lineno:4d} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{asctime}] {levelname} {name} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "format": "[{asctime}] {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },

    "handlers": {
        "stdout": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json" if _prod else "simple",
        },
        "stderr": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "verbose",
        },
        "app_file": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "verbose",
        },
        "request_file": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "access",
            "filters": ["skip_static_requests"],
        },
        "celery_file": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "verbose",
        },
        "structured": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json",
        },
        "dev_console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["require_debug_true"],
        },
    },

    "loggers": {
        "": {
            "handlers": ["stdout", "stderr"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["stdout", "stderr"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["request_file", "error_file", "stderr"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["stdout", "stderr"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["stdout"],
            "level": "WARNING",
            "propagate": False,
        },
        "accounts": {
            "handlers": ["app_file", "error_file", "structured"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "cms": {
            "handlers": ["app_file", "error_file", "structured"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "resources": {
            "handlers": ["app_file", "error_file", "structured"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["celery_file", "stdout", "stderr"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

SLOW_REQUEST_THRESHOLD: float = 4.0

# ──────────────────────────────────────────────────────────────────────────────
# 15. DJANGO-AXES (brute-force login protection)
# ──────────────────────────────────────────────────────────────────────────────
AXES_FAILURE_LIMIT: int = 4
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = ["ip_address", ["username", "user_agent"]]
AXES_ACCESS_FAILURE_LOG_PER_USER_LIMIT: int = 250
AXES_LOCKOUT_TEMPLATE = str(BASE_DIR / "website/templates/axes/lockout.html")
AXES_RESET_ON_SUCCESS: bool = True

# ──────────────────────────────────────────────────────────────────────────────
# 16. RATE LIMITING (django-smart-ratelimit)
# ──────────────────────────────────────────────────────────────────────────────
RATELIMIT_BACKEND = "redis" if _redis_url else "cache"
RATELIMIT_REDIS = {
    "host": os.getenv("REDIS_HOST"),
    "port": 6379,
    "db": 4,
    "password": _redis_password or None,
    "socket_timeout": 0.1,
    "socket_connect_timeout": 0.1,
    "socket_keepalive": True,
    "health_check_interval": 30,
}

RATELIMIT_MIDDLEWARE = {
    "DEFAULT_RATE": "60/m",
    "SKIP_PATHS": ["/admin/", "/health/", "/static/", "/favicon.ico", "/media/"],
    "BLOCK": True,
    "KEY_FUNCTION": "django_smart_ratelimit.utils.get_ip_key",
}

# ──────────────────────────────────────────────────────────────────────────────
# 17. SENTRY
# ──────────────────────────────────────────────────────────────────────────────
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=True,
        environment=environment,
    )

# ──────────────────────────────────────────────────────────────────────────────
# 18. THIRD-PARTY APP SETTINGS
# ──────────────────────────────────────────────────────────────────────────────

# TinyMCE rich-text editor (used in CMS Page admin)
TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 800,
    "width": 1100,
    "menubar": "file edit view insert format tools table help",
    "plugins": (
        "accordion autosave autoresize advlist autolink lists link image charmap "
        "preview anchor searchreplace visualblocks fullscreen insertdatetime media "
        "table code help wordcount save"
    ),
    "toolbar": (
        "undo redo | bold italic underline strikethrough | fontselect fontsizeselect "
        "formatselect | alignleft aligncenter alignright alignjustify | outdent indent | "
        "numlist bullist | forecolor backcolor removeformat | pagebreak | charmap | "
        "fullscreen preview save | insertfile image media link | code"
    ),
    "content_style": "body { font-family: Inter, sans-serif; font-size: 14px; }",
    "custom_undo_redo_levels": 10,
}
TINYMCE_COMPRESSOR: bool = False

# django-taggit: case-insensitive tags
TAGGIT_CASE_INSENSITIVE: bool = True

# ──────────────────────────────────────────────────────────────────────────────
# 19. DATABASE BACKUPS (django-dbbackup)
# ──────────────────────────────────────────────────────────────────────────────
DBBACKUP_CLEANUP_KEEP: int = 7
DBBACKUP_CLEANUP_KEEP_MEDIA: int = 0
DBBACKUP_CONNECTORS = {
    "default": {"CONNECTOR": "dbbackup.db.postgresql.PgDumpConnector"}
}
DBBACKUP_FILENAME_TEMPLATE = "{databasename}-{datetime}.{extension}"
DBBACKUP_DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"
DBBACKUP_DATABASES = ["default"]


# ──────────────────────────────────────────────────────────────────────────────
# 20. MISC / SITE IDENTITY
# ──────────────────────────────────────────────────────────────────────────────
SITE_URL: str = os.getenv("SITE_URL")
SITE_NAME: str = os.getenv("SITE_NAME")
ADMINS: list[tuple[str, str]] = [(os.getenv("ADMIN_NAME"), os.getenv("ADMIN_EMAIL"))]

PHONENUMBER_DB_FORMAT: str = "E164"

# ──────────────────────────────────────────────────────────────────────────────
# 21. ENVIRONMENT-SPECIFIC OVERRIDES
# ──────────────────────────────────────────────────────────────────────────────
if _prod:
    # --- Security hardening ---
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_AGE = 1_209_600  # 2 weeks
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

    # Remove dev_console handler in production loggers
    for _logger_cfg in LOGGING["loggers"].values():
        if "dev_console" in _logger_cfg.get("handlers", []):
            _logger_cfg["handlers"].remove("dev_console")

    # Ensure debug is disabled in production
    DEBUG = False

    if _private_r2 and _public_r2:
        # ── Full dual-bucket production setup ─────────────────────────────────────
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
            # Protected uploads (e.g. admin-only docs) — private bucket, /protected/ prefix
            "protected": {
                "BACKEND": "helpers.cloudflare.storages.ProtectedMediaStorage",
                "OPTIONS": _cf_settings.CLOUDFLARE_R2_CONFIG_OPTIONS,
            },
            # Publicly readable files (e.g. thumbnails, open resources) — public bucket
            "public_files": {
                "BACKEND": "helpers.cloudflare.storages.PublicFilesStorage",
                "OPTIONS": _cf_settings.CLOUDFLARE_R2_PUBLIC_CONFIG_OPTIONS,
            },
            # Database backups — dedicated isolated bucket
            "dbbackup": {
                "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
                "OPTIONS": _BACKUP_R2_OPTIONS,
            },
        }

        MIDDLEWARE = MAIN_MIDDLEWARE

        # Page-level caching middleware (correct insertion order)
        MIDDLEWARE.insert(1, "django.middleware.cache.UpdateCacheMiddleware")
        MIDDLEWARE.append("django.middleware.cache.FetchFromCacheMiddleware")
else:
    # --- Development ---
    if DEBUG:
        LOGGING["loggers"][""]["level"] = "DEBUG"

    # Silk profiler — only in dev
    SILKY_PYTHON_PROFILER = True

    # ── Local filesystem (development default) ────────────────────────────────
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        "protected": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "public_files": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "dbbackup": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": _BACKUP_R2_OPTIONS,
        },
    }

    INSTALLED_APPS: list[str] = DEFAULT_APPS + THIRD_PARTY_APPS + MY_APPS + LOCAL_APPS
    MAIN_MIDDLEWARE.insert(0, "cbe_res_hub.middleware.DisableBrowserCacheMiddleware")
    MIDDLEWARE: list[str] = MAIN_MIDDLEWARE + LOCAL_MIDDLEWARE

# ──────────────────────────────────────────────────────────────────────────────
# 22. TEST OVERRIDES
# ──────────────────────────────────────────────────────────────────────────────
if "pytest" in sys.modules or "test" in sys.argv:
    RATELIMIT_MIDDLEWARE = {
        "DEFAULT_RATE": "120/m",
        "SKIP_PATHS": ["/admin/", "/health/", "/static/", "/favicon.ico", "/media/"],
        "BLOCK": False,
        "KEY_FUNCTION": "django_smart_ratelimit.utils.get_ip_key",
    }
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

    INSTALLED_APPS = DEFAULT_APPS + MY_APPS + THIRD_PARTY_APPS
    MIDDLEWARE = MAIN_MIDDLEWARE

cache_timeout_env_var = os.getenv("CACHE_TIMEOUT")
CACHE_TIMEOUT: int = int(cache_timeout_env_var) if cache_timeout_env_var else 2419200

contact_email_env_var = os.getenv("CONTACT_EMAIL")
CONTACT_EMAIL: str = str(contact_email_env_var) if contact_email_env_var else ""

contact_phone_env_var = os.getenv("CONTACT_PHONE")
CONTACT_PHONE: str = str(contact_phone_env_var) if contact_phone_env_var else ""


# ──────────────────────────────────────────────────────────────────────────────
# Quick reference
#   daphne -p 8000 cbe_res_hub.asgi:application
#   celery -A cbe_res_hub worker -l INFO
#   celery -A cbe_res_hub beat -l INFO
#   python -c "import secrets; print(secrets.token_urlsafe(64))"
# ──────────────────────────────────────────────────────────────────────────────
