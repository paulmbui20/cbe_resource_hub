"""
base.py — shared settings loaded by every environment.
"""

import ast
import os
import ssl
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


# ── Helpers ───────────────────────────────────────────────────────────────────

def require_env(name: str, default: str | None = None) -> str:
    """Get an env var or raise RuntimeError if missing and no default given."""
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# ── Resolve environment ────────────────────────────────────────────────────────
environment: str = require_env("ENVIRONMENT")
_prod: bool = environment == "production"
_testing: bool = environment == "testing"

# ──────────────────────────────────────────────────────────────────────────────
# 1. CORE / SECURITY
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY: str = require_env("SECRET_KEY")

debug_env = os.getenv("DEBUG", "False")
DEBUG: bool = ast.literal_eval(debug_env) if debug_env else False
if (_prod or _testing) and DEBUG:
    raise RuntimeError("DEBUG must be False in production and testing environments")

allowed_hosts = require_env("ALLOWED_HOSTS")
ALLOWED_HOSTS: list[str] = [h.strip() for h in allowed_hosts.split(",") if h.strip()]

csrf_origins = os.getenv("CSRF_ORIGINS", "")
CSRF_TRUSTED_ORIGINS: list[str] = (
    [h.strip() for h in csrf_origins.split(",") if h.strip()] if csrf_origins else []
)

INTERNAL_IPS: list[str] = ["127.0.0.1"]

# ──────────────────────────────────────────────────────────────────────────────
# 2. APPLICATION DEFINITION
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS: list[str] = [
    "allauth_ui",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "slippers",
    "tinymce",
    "taggit",
    "widget_tweaks",
    "django_celery_results",
    "django_celery_beat",
    "storages",
    "axes",
    "django_smart_ratelimit",
    "dbbackup",
]

MY_APPS: list[str] = [
    "accounts.apps.AccountsConfig",
    "cms.apps.CmsConfig",
    "resources.apps.ResourcesConfig",
    "website.apps.WebsiteConfig",
    "files.apps.FilesConfig",
    "seo.apps.SeoConfig",
    "notifications.apps.NotificationsConfig",
    "core.apps.CoreConfig",
]

WAGTAIL_APPS: list[str] = [
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "wagtail.locales",
]

INSTALLED_APPS: list[str] = DEFAULT_APPS + THIRD_PARTY_APPS + WAGTAIL_APPS + MY_APPS

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
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

# MIDDLEWARE is overridden in each environment module.
MIDDLEWARE: list[str] = MAIN_MIDDLEWARE

ROOT_URLCONF = "cbe_res_hub.urls"
WSGI_APPLICATION = "cbe_res_hub.wsgi.application"

# ──────────────────────────────────────────────────────────────────────────────
# 4. TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "website/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cms.context_processors.global_settings",
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ──────────────────────────────────────────────────────────────────────────────
# 6. CACHE  (Redis)
# ──────────────────────────────────────────────────────────────────────────────
_redis_url: str = require_env("REDIS_URL")
_redis_password: str = os.getenv("REDIS_PASSWORD", "")
_redis_port_raw = os.getenv("REDIS_PORT")
_redis_port: int | None = int(_redis_port_raw) if _redis_port_raw else None
_redis_host: str = require_env("REDIS_HOST")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{_redis_url}/0",
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

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

# ──────────────────────────────────────────────────────────────────────────────
# 7. STORAGE — resolved per environment; base leaves STORAGES unset so that
#    each environment module sets the correct backend. The Cloudflare helper
#    module is imported here so environment modules can reference it freely.
# ──────────────────────────────────────────────────────────────────────────────
from helpers.cloudflare import settings as _cf_settings  # noqa: E402

_private_r2 = bool(_cf_settings.CLOUDFLARE_R2_CONFIG_OPTIONS)
_public_r2 = bool(_cf_settings.CLOUDFLARE_R2_PUBLIC_CONFIG_OPTIONS)
_backup_r2 = bool(_cf_settings.CLOUDFLARE_R2_BACKUP_CONFIG_OPTIONS)

# ──────────────────────────────────────────────────────────────────────────────
# 8. STATIC & MEDIA
# ──────────────────────────────────────────────────────────────────────────────
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_DIRS = [
    BASE_DIR / "website/static",
    "seo/static",
]
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)
STATIC_URL = "static/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# ──────────────────────────────────────────────────────────────────────────────
# 9. AUTHENTICATION
# ──────────────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.CustomUser"
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
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID: int = int(os.getenv("SITE_ID", "1"))

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "optional")
LOGIN_ON_EMAIL_CONFIRMATION = True
LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_SESSION_REMEMBER = True
LOGOUT_ON_GET = True

ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/5m/ip",
    "change_password": "3/m/user",
    "reset_password": "3/m/ip",
    "signup": "5/m/ip",
    "confirm_email": "3/m/user",
}

ACCOUNT_ADAPTER = "accounts.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "accounts.adapters.SocialAccountAdapter"
ALLAUTH_UI_THEME = "dark"

GOOGLE_OAUTH_CLIENT_ID = require_env("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = require_env("GOOGLE_OAUTH_CLIENT_SECRET")

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
        "EMAIL_AUTHENTICATION": True,
    }
}

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# ──────────────────────────────────────────────────────────────────────────────
# 10. INTERNATIONALISATION
# ──────────────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en", "English"),
    ("sw", "Swahili"),
]
LANGUAGES_BIDI: list = []
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────────────────────────────────────
# 11. EMAIL
# ──────────────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST: str = require_env("EMAIL_HOST")
EMAIL_PORT: int = int(require_env("EMAIL_PORT"))
_email_tls = require_env("EMAIL_USE_TLS")
EMAIL_USE_TLS: bool = ast.literal_eval(_email_tls) if _email_tls else True
EMAIL_HOST_USER: str = require_env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD: str = require_env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL: str = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# ──────────────────────────────────────────────────────────────────────────────
# 12. CELERY
# ──────────────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL: str = f"{_redis_url}/1"
CELERY_RESULT_BACKEND: str = f"{_redis_url}/2"
CELERY_ACCEPT_CONTENT: list[str] = ["json"]
CELERY_TASK_SERIALIZER: str = "json"
CELERY_RESULT_SERIALIZER: str = "json"
CELERY_TIMEZONE: str = TIME_ZONE
CELERY_TASK_TRACK_STARTED: bool = True
CELERY_TASK_TIME_LIMIT: int = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60

if _redis_url and _redis_url.startswith("rediss://"):
    _ssl_config = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
    CELERY_BROKER_USE_SSL = _ssl_config
    CELERY_REDIS_BACKEND_USE_SSL = _ssl_config

# ──────────────────────────────────────────────────────────────────────────────
# 13. ASGI
# ──────────────────────────────────────────────────────────────────────────────
ASGI_APPLICATION = "cbe_res_hub.asgi.application"

# ──────────────────────────────────────────────────────────────────────────────
# 14. LOGGING
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
            "()": "pythonjsonlogger.json.JsonFormatter",
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
# 15. DJANGO-AXES
# ──────────────────────────────────────────────────────────────────────────────
AXES_FAILURE_LIMIT: int = 4
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = ["ip_address", ["username", "user_agent"]]
AXES_ACCESS_FAILURE_LOG_PER_USER_LIMIT: int = 250
AXES_LOCKOUT_TEMPLATE = str(BASE_DIR / "website/templates/axes/lockout.html")
AXES_RESET_ON_SUCCESS: bool = True

# ──────────────────────────────────────────────────────────────────────────────
# 16. RATE LIMITING
# ──────────────────────────────────────────────────────────────────────────────
RATELIMIT_BACKEND = "redis" if _redis_url else "cache"
RATELIMIT_REDIS = {
    "host": _redis_host,
    "port": _redis_port,
    "db": 3,
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
# 17. THIRD-PARTY APP SETTINGS
# ──────────────────────────────────────────────────────────────────────────────
TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 800,
    "width": "100%",
    "min_width": 800,
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
TAGGIT_CASE_INSENSITIVE: bool = True

# ──────────────────────────────────────────────────────────────────────────────
# 20. MISC / SITE IDENTITY
# ──────────────────────────────────────────────────────────────────────────────
SITE_URL: str = require_env("SITE_URL")
SITE_NAME: str = require_env("SITE_NAME")
admin_email = require_env("ADMIN_EMAIL")
ADMINS: list[tuple[str, str]] = [(require_env("ADMIN_NAME"), admin_email)]
SERVER_EMAIL: str = admin_email
PHONENUMBER_DB_FORMAT: str = "E164"

cache_timeout_env_var = os.getenv("CACHE_TIMEOUT")
CACHE_TIMEOUT: int = int(cache_timeout_env_var) if cache_timeout_env_var else 2419200

contact_email_env_var = os.getenv("CONTACT_EMAIL")
CONTACT_EMAIL: str = str(contact_email_env_var) if contact_email_env_var else ""

contact_phone_env_var = os.getenv("CONTACT_PHONE")
CONTACT_PHONE: str = str(contact_phone_env_var) if contact_phone_env_var else ""

# ──────────────────────────────────────────────────────────────────────────────
# 21. WAGTAIL
# ──────────────────────────────────────────────────────────────────────────────
WAGTAIL_SITE_NAME = "CBE Resource Hub"
WAGTAILADMIN_BASE_URL = SITE_URL
WAGTAILDOCS_SERVE_METHOD = "direct"

WAGTAILIMAGES_IMAGE_MODEL = 'website.CustomImage'
WAGTAILDOCS_DOCUMENT_MODEL = 'website.CustomDocument'
