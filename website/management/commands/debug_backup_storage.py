"""
Debug command to inspect backup storage configuration
Usage: python manage.py debug_backup_storage
"""
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug backup storage configuration and list all files'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== Backup Storage Debug Info ===\n'))

        try:
            from django.core.files.storage import storages

            # Get the storage configuration
            storage = storages['dbbackup']

            self.stdout.write(self.style.SUCCESS(f'Storage Backend: {storage.__class__.__name__}'))

            # Try to access storage attributes
            if hasattr(storage, 'bucket_name'):
                self.stdout.write(f'Bucket Name: {storage.bucket_name}')
            if hasattr(storage, 'location'):
                self.stdout.write(f'Location: {storage.location}')
            if hasattr(storage, 'endpoint_url'):
                self.stdout.write(f'Endpoint URL: {storage.endpoint_url}')

            self.stdout.write('\n--- Attempting to list files at different paths ---\n')

            # Try listing at root
            self.stdout.write(self.style.WARNING("Listing root ('')..."))
            try:
                dirs, files = storage.listdir('')
                self.stdout.write(f'  Directories: {dirs}')
                self.stdout.write(f'  Files: {files[:10] if len(files) > 10 else files}')
                self.stdout.write(f'  Total files: {len(files)}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))

            # Try listing database-backups/
            self.stdout.write(self.style.WARNING("\nListing 'database-backups'..."))
            try:
                dirs, files = storage.listdir('database-backups')
                self.stdout.write(f'  Directories: {dirs}')
                self.stdout.write(f'  Files: {files[:10] if len(files) > 10 else files}')
                self.stdout.write(f'  Total files: {len(files)}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))

            # Try listing database-backups/ (with trailing slash)
            self.stdout.write(self.style.WARNING("\nListing 'database-backups/'..."))
            try:
                dirs, files = storage.listdir('database-backups/')
                self.stdout.write(f'  Directories: {dirs}')
                self.stdout.write(f'  Files: {files[:10] if len(files) > 10 else files}')
                self.stdout.write(f'  Total files: {len(files)}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))

            # Try to use boto3 directly to list bucket contents
            self.stdout.write(self.style.WARNING('\n--- Using boto3 directly ---'))
            try:
                import boto3
                from botocore.config import Config

                # Get credentials from storage
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=storage.access_key,
                    aws_secret_access_key=storage.secret_key,
                    endpoint_url=storage.endpoint_url,
                    region_name=storage.region_name,
                    config=Config(signature_version='s3v4')
                )

                # List all objects in bucket
                self.stdout.write(f'\nListing all objects in bucket: {storage.bucket_name}')
                response = s3_client.list_objects_v2(
                    Bucket=storage.bucket_name,
                    MaxKeys=100
                )

                if 'Contents' in response:
                    self.stdout.write(f'Found {len(response["Contents"])} objects:')
                    for obj in response['Contents']:
                        self.stdout.write(f'  - {obj["Key"]} ({obj["Size"]} bytes)')
                else:
                    self.stdout.write('No objects found in bucket')

                # List with database-backups prefix
                self.stdout.write(f'\nListing objects with prefix "database-backups/"')
                response = s3_client.list_objects_v2(
                    Bucket=storage.bucket_name,
                    Prefix='database-backups/',
                    MaxKeys=100
                )

                if 'Contents' in response:
                    self.stdout.write(f'Found {len(response["Contents"])} objects:')
                    for obj in response['Contents']:
                        self.stdout.write(f'  - {obj["Key"]} ({obj["Size"]} bytes)')
                else:
                    self.stdout.write('No objects found with this prefix')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error using boto3: {str(e)}'))

            # Show STORAGES configuration
            self.stdout.write(self.style.WARNING('\n--- STORAGES Configuration ---'))
            if hasattr(settings, 'STORAGES'):
                if 'dbbackup' in settings.STORAGES:
                    config = settings.STORAGES['dbbackup']
                    self.stdout.write(f'Backend: {config.get("BACKEND")}')
                    self.stdout.write(f'OPTIONS:')
                    for key, value in config.get('OPTIONS', {}).items():
                        # Hide sensitive values
                        if 'key' in key.lower() or 'secret' in key.lower():
                            self.stdout.write(f'  {key}: ***HIDDEN***')
                        else:
                            self.stdout.write(f'  {key}: {value}')
                else:
                    self.stdout.write(self.style.ERROR('No "dbbackup" key in STORAGES'))
            else:
                self.stdout.write(self.style.ERROR('STORAGES not configured'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nFatal error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
