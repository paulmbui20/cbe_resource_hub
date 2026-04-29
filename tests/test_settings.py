"""
tests/test_settings.py

Validates that the Django settings are correctly configured for the testing
environment. These tests catch mis-configurations before they cause cryptic
runtime failures.

Covers:
  - Installed apps: all project apps present, no duplicates
  - Middleware: all required middleware present, correct relative order
  - Authentication: custom user model, login URLs, auth backends
  - Database: SQLite in testing, USE_TZ enabled
  - Cache: Redis backend configured with expected keys
  - Storage: all 5 storage backends defined in testing
  - Celery: eager execution in testing
  - Allauth: email-based login, correct adapters
  - Axes: failure limit, cooloff, lockout template
  - Rate limiting: non-blocking in tests
  - Internationalisation: timezone, language
  - Static/media paths defined
  - Logging: standard loggers present
  - Custom settings: SITE_NAME, SITE_URL, CACHE_TIMEOUT, PHONENUMBER_DB_FORMAT
"""

from django.conf import settings
from django.test import TestCase


class InstalledAppsTests(TestCase):
    """All expected apps are in INSTALLED_APPS."""

    REQUIRED_DJANGO_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.sites",
        "django.contrib.sitemaps",
    ]

    REQUIRED_THIRD_PARTY = [
        "allauth",
        "allauth.account",
        "axes",
        "storages",
        "tinymce",
        "taggit",
    ]

    REQUIRED_MY_APPS = [
        "accounts.apps.AccountsConfig",
        "cms.apps.CmsConfig",
        "resources.apps.ResourcesConfig",
        "website.apps.WebsiteConfig",
        "files.apps.FilesConfig",
        "seo.apps.SeoConfig",
        "notifications.apps.NotificationsConfig",
        "core.apps.CoreConfig",
    ]

    def test_no_duplicates_in_installed_apps(self):
        apps = settings.INSTALLED_APPS
        self.assertEqual(len(apps), len(set(apps)), "Duplicate entries in INSTALLED_APPS")

    def test_django_core_apps_present(self):
        for app in self.REQUIRED_DJANGO_APPS:
            self.assertIn(app, settings.INSTALLED_APPS, f"Missing Django app: {app}")

    def test_third_party_apps_present(self):
        for app in self.REQUIRED_THIRD_PARTY:
            self.assertIn(app, settings.INSTALLED_APPS, f"Missing third-party app: {app}")

    def test_project_apps_present(self):
        for app in self.REQUIRED_MY_APPS:
            self.assertIn(app, settings.INSTALLED_APPS, f"Missing project app: {app}")

    def test_contenttypes_and_auth_both_present(self):
        """Both contenttypes and auth must be installed (order is environment-specific)."""
        self.assertIn("django.contrib.contenttypes", settings.INSTALLED_APPS)
        self.assertIn("django.contrib.auth", settings.INSTALLED_APPS)


class MiddlewareTests(TestCase):
    """Middleware stack is correctly ordered."""

    def test_security_middleware_present(self):
        self.assertIn("django.middleware.security.SecurityMiddleware", settings.MIDDLEWARE)

    def test_session_middleware_present(self):
        self.assertIn("django.contrib.sessions.middleware.SessionMiddleware", settings.MIDDLEWARE)

    def test_csrf_middleware_present(self):
        self.assertIn("django.middleware.csrf.CsrfViewMiddleware", settings.MIDDLEWARE)

    def test_auth_middleware_present(self):
        self.assertIn("django.contrib.auth.middleware.AuthenticationMiddleware", settings.MIDDLEWARE)

    def test_message_middleware_present(self):
        self.assertIn("django.contrib.messages.middleware.MessageMiddleware", settings.MIDDLEWARE)

    def test_axes_middleware_present(self):
        self.assertIn("axes.middleware.AxesMiddleware", settings.MIDDLEWARE)

    def test_slug_redirect_middleware_present(self):
        self.assertIn("seo.middleware.SlugRedirectMiddleware", settings.MIDDLEWARE)

    def test_allauth_middleware_present(self):
        self.assertIn("allauth.account.middleware.AccountMiddleware", settings.MIDDLEWARE)

    def test_gzip_middleware_present(self):
        self.assertIn("django.middleware.gzip.GZipMiddleware", settings.MIDDLEWARE)

    def test_session_before_auth(self):
        mw = list(settings.MIDDLEWARE)
        session_idx = mw.index("django.contrib.sessions.middleware.SessionMiddleware")
        auth_idx = mw.index("django.contrib.auth.middleware.AuthenticationMiddleware")
        self.assertLess(session_idx, auth_idx)

    def test_csrf_before_auth(self):
        mw = list(settings.MIDDLEWARE)
        csrf_idx = mw.index("django.middleware.csrf.CsrfViewMiddleware")
        auth_idx = mw.index("django.contrib.auth.middleware.AuthenticationMiddleware")
        self.assertLess(csrf_idx, auth_idx)


class DatabaseTests(TestCase):
    """Database is correctly configured for testing."""

    def test_default_database_exists(self):
        self.assertIn("default", settings.DATABASES)

    def test_sqlite_backend_in_testing(self):
        db = settings.DATABASES["default"]
        self.assertEqual(db["ENGINE"], "django.db.backends.sqlite3")

    def test_use_tz_enabled(self):
        self.assertTrue(settings.USE_TZ)

    def test_default_auto_field_is_big_auto(self):
        self.assertEqual(settings.DEFAULT_AUTO_FIELD, "django.db.models.BigAutoField")


class CacheTests(TestCase):
    """Cache backend is properly configured."""

    def test_default_cache_exists(self):
        self.assertIn("default", settings.CACHES)

    def test_redis_backend_configured(self):
        backend = settings.CACHES["default"]["BACKEND"]
        self.assertIn("redis", backend.lower())

    def test_cache_key_prefix_set(self):
        self.assertEqual(settings.CACHES["default"].get("KEY_PREFIX"), "cbe")

    def test_cache_timeout_set(self):
        self.assertIn("TIMEOUT", settings.CACHES["default"])
        self.assertGreater(settings.CACHES["default"]["TIMEOUT"], 0)

    def test_session_engine_uses_cached_db(self):
        self.assertEqual(settings.SESSION_ENGINE, "django.contrib.sessions.backends.cached_db")


class StorageTests(TestCase):
    """Storage backends are all defined and use filesystem in testing."""

    REQUIRED_STORAGES = ["default", "staticfiles", "public_files", "protected", "dbbackup"]

    def test_all_storages_defined(self):
        for key in self.REQUIRED_STORAGES:
            self.assertIn(key, settings.STORAGES, f"Missing storage: {key}")

    def test_default_storage_uses_filesystem_in_testing(self):
        backend = settings.STORAGES["default"]["BACKEND"]
        self.assertIn("FileSystemStorage", backend)

    def test_public_files_uses_filesystem_in_testing(self):
        backend = settings.STORAGES["public_files"]["BACKEND"]
        self.assertIn("FileSystemStorage", backend)

    def test_staticfiles_storage_defined(self):
        self.assertIn("staticfiles", settings.STORAGES)

    def test_each_storage_has_backend_key(self):
        for key, config in settings.STORAGES.items():
            self.assertIn("BACKEND", config, f"Storage '{key}' missing BACKEND")


class AuthenticationTests(TestCase):
    """Authentication is correctly configured."""

    def test_custom_user_model(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.CustomUser")

    def test_login_url(self):
        self.assertEqual(settings.LOGIN_URL, "/accounts/login/")

    def test_login_redirect_url(self):
        self.assertEqual(settings.LOGIN_REDIRECT_URL, "accounts:dashboard")

    def test_logout_redirect_url(self):
        self.assertEqual(settings.LOGOUT_REDIRECT_URL, "/")

    def test_axes_backend_in_auth_backends(self):
        self.assertIn("axes.backends.AxesStandaloneBackend", settings.AUTHENTICATION_BACKENDS)

    def test_django_model_backend_in_auth_backends(self):
        self.assertIn("django.contrib.auth.backends.ModelBackend", settings.AUTHENTICATION_BACKENDS)

    def test_allauth_backend_in_auth_backends(self):
        self.assertIn("allauth.account.auth_backends.AuthenticationBackend",
                      settings.AUTHENTICATION_BACKENDS)

    def test_axes_backend_first(self):
        """Axes must be first so it can block before any auth check."""
        backends = list(settings.AUTHENTICATION_BACKENDS)
        self.assertEqual(backends[0], "axes.backends.AxesStandaloneBackend")

    def test_password_validators_present(self):
        self.assertTrue(len(settings.AUTH_PASSWORD_VALIDATORS) >= 4)

    def test_minimum_length_validator_present(self):
        names = [v["NAME"] for v in settings.AUTH_PASSWORD_VALIDATORS]
        self.assertIn("django.contrib.auth.password_validation.MinimumLengthValidator", names)


class AllauthTests(TestCase):
    """django-allauth is configured for email-based login."""

    def test_email_login_method(self):
        self.assertIn("email", settings.ACCOUNT_LOGIN_METHODS)

    def test_unique_email_required(self):
        self.assertTrue(settings.ACCOUNT_UNIQUE_EMAIL)

    def test_session_remember_enabled(self):
        self.assertTrue(settings.ACCOUNT_SESSION_REMEMBER)

    def test_account_adapter_set(self):
        self.assertEqual(settings.ACCOUNT_ADAPTER, "accounts.adapters.AccountAdapter")

    def test_social_account_adapter_set(self):
        self.assertEqual(settings.SOCIALACCOUNT_ADAPTER, "accounts.adapters.SocialAccountAdapter")


class AxesTests(TestCase):
    """django-axes brute-force protection is configured."""

    def test_failure_limit(self):
        self.assertEqual(settings.AXES_FAILURE_LIMIT, 4)

    def test_cooloff_time_set(self):
        from datetime import timedelta
        self.assertIsInstance(settings.AXES_COOLOFF_TIME, timedelta)
        self.assertGreater(settings.AXES_COOLOFF_TIME.total_seconds(), 0)

    def test_lockout_parameters_set(self):
        self.assertIsNotNone(settings.AXES_LOCKOUT_PARAMETERS)
        self.assertIn("ip_address", settings.AXES_LOCKOUT_PARAMETERS)

    def test_reset_on_success(self):
        self.assertTrue(settings.AXES_RESET_ON_SUCCESS)


class CeleryTests(TestCase):
    """Celery runs eagerly in the test environment."""

    def test_task_always_eager(self):
        self.assertTrue(getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False))

    def test_eager_propagates(self):
        self.assertTrue(getattr(settings, "CELERY_TASK_EAGER_PROPAGATES", False))

    def test_celery_timezone_matches_django(self):
        self.assertEqual(getattr(settings, "CELERY_TIMEZONE", None), settings.TIME_ZONE)

    def test_celery_uses_json_serializer(self):
        self.assertEqual(settings.CELERY_TASK_SERIALIZER, "json")
        self.assertEqual(settings.CELERY_RESULT_SERIALIZER, "json")
        self.assertIn("json", settings.CELERY_ACCEPT_CONTENT)


class InternationalisationTests(TestCase):
    """i18n settings are correct."""

    def test_timezone_is_nairobi(self):
        self.assertEqual(settings.TIME_ZONE, "Africa/Nairobi")

    def test_use_i18n(self):
        self.assertTrue(settings.USE_I18N)

    def test_use_tz(self):
        self.assertTrue(settings.USE_TZ)

    def test_language_code(self):
        self.assertEqual(settings.LANGUAGE_CODE, "en-us")

    def test_phonenumber_format(self):
        self.assertEqual(settings.PHONENUMBER_DB_FORMAT, "E164")


class StaticMediaTests(TestCase):
    """Static and media file paths are set."""

    def test_static_url_set(self):
        self.assertIsNotNone(settings.STATIC_URL)

    def test_media_url_set(self):
        self.assertEqual(settings.MEDIA_URL, "/media/")

    def test_static_root_set(self):
        self.assertIsNotNone(settings.STATIC_ROOT)

    def test_media_root_set(self):
        self.assertIsNotNone(settings.MEDIA_ROOT)

    def test_staticfiles_finders_set(self):
        self.assertIn(
            "django.contrib.staticfiles.finders.FileSystemFinder",
            settings.STATICFILES_FINDERS,
        )


class TemplateTests(TestCase):
    """Template backend and context processors are set."""

    def test_django_template_backend(self):
        backends = [t["BACKEND"] for t in settings.TEMPLATES]
        self.assertIn("django.template.backends.django.DjangoTemplates", backends)

    def test_required_context_processors(self):
        processors = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
        self.assertIn("django.template.context_processors.request", processors)
        self.assertIn("django.contrib.auth.context_processors.auth", processors)
        self.assertIn("django.contrib.messages.context_processors.messages", processors)

    def test_cms_context_processor(self):
        processors = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
        self.assertIn("cms.context_processors.global_settings", processors)


class SiteIdentityTests(TestCase):
    """Project identity settings are set."""

    def test_site_id_is_int(self):
        self.assertIsInstance(settings.SITE_ID, int)

    def test_site_name_set(self):
        self.assertTrue(hasattr(settings, "SITE_NAME"))
        self.assertIsNotNone(settings.SITE_NAME)

    def test_site_url_set(self):
        self.assertTrue(hasattr(settings, "SITE_URL"))
        self.assertIsNotNone(settings.SITE_URL)

    def test_cache_timeout_is_positive(self):
        self.assertGreater(settings.CACHE_TIMEOUT, 0)

    def test_root_urlconf(self):
        self.assertEqual(settings.ROOT_URLCONF, "cbe_res_hub.urls")


class LoggingTests(TestCase):
    """Logging configuration has required loggers and handlers."""

    def test_logging_version(self):
        self.assertEqual(settings.LOGGING["version"], 1)

    def test_disable_existing_loggers_false(self):
        self.assertFalse(settings.LOGGING["disable_existing_loggers"])

    def test_stdout_handler_present(self):
        self.assertIn("stdout", settings.LOGGING["handlers"])

    def test_stderr_handler_present(self):
        self.assertIn("stderr", settings.LOGGING["handlers"])

    def test_root_logger_present(self):
        self.assertIn("", settings.LOGGING["loggers"])

    def test_django_logger_present(self):
        self.assertIn("django", settings.LOGGING["loggers"])

    def test_accounts_logger_present(self):
        self.assertIn("accounts", settings.LOGGING["loggers"])

    def test_celery_logger_present(self):
        self.assertIn("celery", settings.LOGGING["loggers"])

    def test_resources_logger_present(self):
        self.assertIn("resources", settings.LOGGING["loggers"])


class RateLimitingTests(TestCase):
    """Rate limiting is non-blocking in tests."""

    def test_ratelimit_middleware_defined(self):
        self.assertTrue(hasattr(settings, "RATELIMIT_MIDDLEWARE"))

    def test_ratelimit_not_blocking_in_tests(self):
        self.assertFalse(settings.RATELIMIT_MIDDLEWARE.get("BLOCK", True))

    def test_default_rate_set(self):
        self.assertIn("DEFAULT_RATE", settings.RATELIMIT_MIDDLEWARE)

    def test_skip_paths_includes_health(self):
        skip_paths = settings.RATELIMIT_MIDDLEWARE.get("SKIP_PATHS", [])
        self.assertTrue(any("health" in p for p in skip_paths))
