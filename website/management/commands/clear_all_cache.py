from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Clear all Django cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force clear cache without confirmation',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        if not force:
            confirm = input("This will clear ALL cache. Are you sure? [y/N]: ")
            if confirm.lower() not in ['y', 'yes']:
                self.stdout.write(self.style.WARNING("Cache clearing cancelled."))
                return

        self.stdout.write("Clearing all cache...")

        # Clear all configured cache backends
        try:
            from django.core.cache import caches
            for cache_name in settings.CACHES:
                try:
                    caches[cache_name].clear()
                    self.stdout.write(self.style.SUCCESS(f"✓ {cache_name} cache cleared"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"✗ Error clearing {cache_name} cache: {str(e)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"✗ Error accessing cache backends: {str(e)}"))

        # Clear sessions if using cache-based sessions
        if hasattr(settings, 'SESSION_ENGINE') and 'cache' in settings.SESSION_ENGINE:
            try:
                from django.contrib.sessions.models import Session
                Session.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("✓ Session cache cleared"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"✗ Error clearing session cache: {str(e)}"))

        # Clear content type cache (important after data population)
        try:
            from django.contrib.contenttypes.models import ContentType
            ContentType.objects.clear_cache()
            self.stdout.write(self.style.SUCCESS("✓ Content type cache cleared"))
        except Exception as e:
            self.stderr.write(self.style.WARNING(f"Note: Content type cache not cleared: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("All cache clearing operations completed!"))
