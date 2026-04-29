"""
Django management command for health checks.
Placed in: website/management/commands/check_health.py
Usage: python manage.py check_health
"""
import sys
from datetime import datetime, UTC

from django.core.management.base import BaseCommand
from django.test.client import Client


class Command(BaseCommand):
    help = 'Performs application health checks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--endpoint',
            type=str,
            default='/health/',
            help='Health check endpoint (default: /health/)'
        )
        parser.add_argument(
            '--fail-on-unhealthy',
            action='store_true',
            help='Exit with non-zero status if health check fails'
        )

    def handle(self, *args, **options):
        endpoint = options['endpoint']
        fail_on_unhealthy = options['fail_on_unhealthy']

        self.stdout.write(f"Checking health at: {endpoint}")
        self.stdout.write(f"Timestamp: {datetime.now(UTC).isoformat()}\n")

        client = Client()

        try:
            response = client.get(endpoint)
            data = response.json()

            status = data.get('status')
            checks = data.get('checks', {})

            # Display status
            if status == 'healthy':
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Status: {status}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Status: {status}")
                )

            # Display individual checks
            self.stdout.write("\nDetailed Checks:")
            self.stdout.write("-" * 50)

            for check_name, check_data in checks.items():
                is_healthy = check_data.get('healthy', False)

                if is_healthy:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ {check_name}: healthy")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"✗ {check_name}: unhealthy")
                    )

                # Show detailed info for each check
                if isinstance(check_data, dict):
                    for key, value in check_data.items():
                        if key != 'healthy':
                            self.stdout.write(f"  - {key}: {value}")

            self.stdout.write("-" * 50)

            # Exit with appropriate status
            if fail_on_unhealthy and status != 'healthy':
                self.stdout.write(
                    self.style.ERROR("\nHealth check FAILED")
                )
                sys.exit(1)
            else:
                self.stdout.write(
                    self.style.SUCCESS("\nHealth check completed")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during health check: {str(e)}")
            )
            if fail_on_unhealthy:
                sys.exit(1)
