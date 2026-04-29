# seo/management/commands/clean_slug_redirects.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from seo.models import SlugRedirect


class Command(BaseCommand):
    help = 'Clean up old or unused slug redirects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Remove redirects older than this many days with 0 hits',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - timedelta(days=days)

        # Find old redirects with no hits
        old_redirects = SlugRedirect.objects.filter(
            created_at__lt=cutoff_date,
            hit_count=0
        )

        count = old_redirects.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No old redirects found to clean up')
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} redirects older than {days} days with 0 hits'
                )
            )
            for redirect in old_redirects[:10]:
                self.stdout.write(f'  - {redirect.old_slug} → {redirect.new_slug}')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            old_redirects.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} old redirects'
                )
            )
