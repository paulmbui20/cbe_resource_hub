from django.apps import AppConfig


class CmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cms"

    def ready(self):
        from cms.signals import register_signals  # noqa: PLC0415
        register_signals()
