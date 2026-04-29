"""
Management command for manual database backups
Usage: python manage.py manual_backup [--test]
"""
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from website.tasks import backup_database, test_backup_configuration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manually trigger a database backup to Cloudflare R2'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test backup configuration without creating actual backup',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            dest='use_async',
            help='Run backup as async Celery task',
        )

    def handle(self, *args, **options):
        if options['test']:
            self.stdout.write(self.style.WARNING('Testing backup configuration...'))
            result = test_backup_configuration()

            if result['status'] == 'success':
                self.stdout.write(self.style.SUCCESS('✓ Backup configuration is valid'))
                self.stdout.write(f"  Timestamp: {result['timestamp']}")
            else:
                self.stdout.write(self.style.ERROR('✗ Backup configuration test failed'))
                self.stdout.write(f"  Error: {result.get('error', 'Unknown error')}")
            return

        self.stdout.write(self.style.WARNING('Starting manual database backup...'))
        start_time = timezone.now()

        try:
            if options['use_async']:
                # Run as async Celery task
                task = backup_database.apply_async(
                    kwargs={'backup_type': 'manual'},
                    expires=3600
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Backup task queued: {task.id}')
                )
                self.stdout.write('  Use Celery logs to monitor progress')
            else:
                # Run synchronously
                result = backup_database(backup_type='manual')

                duration = (timezone.now() - start_time).total_seconds()

                self.stdout.write(self.style.SUCCESS('✓ Backup completed successfully'))
                self.stdout.write(f"  Duration: {duration:.2f} seconds")
                self.stdout.write(f"  Timestamp: {result['timestamp']}")
                self.stdout.write(
                    self.style.WARNING(
                        '\nBackup uploaded to Cloudflare R2. '
                        'Verify in your R2 dashboard.'
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Backup failed: {str(e)}'))
            logger.error(f"Manual backup failed: {str(e)}", exc_info=True)
            raise
