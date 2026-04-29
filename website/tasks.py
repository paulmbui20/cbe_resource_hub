"""
Celery health check task.
"""
import logging
from datetime import UTC
from datetime import datetime

import requests
from celery import shared_task
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def backup_database(self, backup_type='daily'):
    """
    Create a database backup and upload to Cloudflare R2

    Args:
        backup_type: 'daily' or 'weekly' for logging purposes
    """
    start_time = timezone.now()

    try:
        logger.info(f"Starting {backup_type} database backup")

        # Create database backup
        call_command(
            'dbbackup',
            '--noinput',
            '--clean',
            '--compress',
            verbosity=2
        )

        duration = (timezone.now() - start_time).total_seconds()
        logger.info(
            f"{backup_type.capitalize()} database backup completed successfully "
            f"in {duration:.2f} seconds"
        )

        return {
            'status': 'success',
            'backup_type': backup_type,
            'duration': duration,
            'timestamp': start_time.isoformat()
        }

    except Exception as exc:
        duration = (timezone.now() - start_time).total_seconds()
        logger.error(
            f"{backup_type.capitalize()} database backup failed after {duration:.2f}s: {str(exc)}",
            exc_info=True
        )

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=min(300 * (2 ** self.request.retries), 3600))


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def cleanup_old_backups(self, keep_days=14):
    """
    Clean up backups older than specified days from R2 storage.
    """
    try:
        logger.info(f"Starting cleanup of backups older than {keep_days} days")

        from django.core.files.storage import storages
        storage = storages['dbbackup']

        # List files in backup root
        directories, files = storage.listdir('')

        # Valid backup extensions
        backup_extensions = ('.psql', '.psql.gz', '.sql', '.sql.gz', '.dump', '.dump.gz')

        now = timezone.now()
        deleted = []
        kept = []

        for file_name in files:
            if not file_name.endswith(backup_extensions):
                continue

            try:
                modified = storage.get_modified_time(file_name)
            except Exception:
                # If modified time can't be read, keep it (fail-safe)
                kept.append(file_name)
                continue

            age_days = (now - modified).days

            if age_days > keep_days:
                try:
                    storage.delete(file_name)
                    deleted.append(file_name)
                except Exception as e:
                    logger.error(f"Failed to delete old backup {file_name}: {e}")
                    kept.append(file_name)
            else:
                kept.append(file_name)

        logger.info(
            f"Backup cleanup completed. Deleted {len(deleted)} old backups, kept {len(kept)}"
        )

        return {
            "status": "success",
            "deleted": deleted,
            "kept": kept,
            "timestamp": timezone.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Backup cleanup failed: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def weekly_full_backup(self):
    """
    Create a weekly full backup with extended retention
    This is a wrapper around backup_database with 'weekly' type
    """
    return backup_database.apply_async(
        kwargs={'backup_type': 'weekly'},
        expires=3600  # Task expires after 1 hour
    )


@shared_task
def test_backup_configuration():
    """
    Test backup configuration without creating actual backup
    Useful for verifying R2 connectivity and permissions
    """
    try:
        logger.info("Testing backup configuration...")

        # Test R2 connection using Django's STORAGES
        from django.core.files.storage import storages

        storage = storages['dbbackup']

        # Try to list files (this will verify credentials and bucket access)
        try:
            list(storage.listdir('database-backups'))
            logger.info("✓ Successfully connected to R2 backup bucket")
        except Exception as e:
            logger.error(f"✗ Failed to list R2 bucket contents: {str(e)}")
            raise

        # Verify database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            logger.info("✓ Database connection successful")

        logger.info("Backup configuration test completed successfully")

        return {
            'status': 'success',
            'message': 'All backup components are properly configured',
            'timestamp': timezone.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Backup configuration test failed: {str(exc)}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def backup_health_check():
    """
    Check the health of backup system
    Verifies last backup time and alerts if backups are failing
    """
    try:
        from django.core.files.storage import storages

        storage = storages['dbbackup']

        # List from root since location is already 'database-backups'
        directories, files = storage.listdir('')

        # Filter for backup files
        backup_extensions = ('.psql', '.psql.gz', '.sql', '.sql.gz', '.dump', '.dump.gz')
        backup_files = [f for f in files if f.endswith(backup_extensions)]

        if not backup_files:
            logger.warning("No backup files found in R2 bucket")
            return {
                'status': 'warning',
                'message': 'No backups found',
                'timestamp': timezone.now().isoformat()
            }

        # Get the most recent backup
        sorted_backups = sorted(backup_files, reverse=True)
        latest_backup = sorted_backups[0] if sorted_backups else None

        if latest_backup:
            try:
                # Check if backup is recent (within last 36 hours for daily backups)
                modified_time = storage.get_modified_time(latest_backup)
                hours_since_backup = (timezone.now() - modified_time).total_seconds() / 3600

                if hours_since_backup > 36:
                    logger.warning(
                        f"Last backup is {hours_since_backup:.1f} hours old. "
                        f"Latest backup: {latest_backup}"
                    )
                    status = 'warning'
                    message = f'Last backup is {hours_since_backup:.1f} hours old'
                else:
                    logger.info(
                        f"Backup system healthy. Last backup: {latest_backup} "
                        f"({hours_since_backup:.1f} hours ago)"
                    )
                    status = 'healthy'
                    message = f'Last backup {hours_since_backup:.1f} hours ago'

                return {
                    'status': status,
                    'message': message,
                    'latest_backup': latest_backup,
                    'hours_since_backup': hours_since_backup,
                    'total_backups': len(backup_files),
                    'timestamp': timezone.now().isoformat()
                }
            except Exception as e:
                logger.warning(f"Could not get backup file info: {str(e)}")
                return {
                    'status': 'warning',
                    'message': f'Found {len(backup_files)} backups but could not verify dates',
                    'latest_backup': latest_backup,
                    'total_backups': len(backup_files),
                    'timestamp': timezone.now().isoformat()
                }

    except Exception as exc:
        logger.error(f"Backup health check failed: {str(exc)}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_kwargs={'max_retries': 3, 'countdown': 30},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def health_check_task(self):
    """
    Periodic health check task that monitors the application's health status.
    This task calls the health check endpoint to verify all services are operational.
    """
    try:
        site_url = settings.SITE_URL.rstrip('/')
        url = f'{site_url}/health/'

        logger.info(f"Starting health check for: {url}")

        response = requests.get(url, timeout=45)
        response.raise_for_status()

        data = response.json()
        timestamp = datetime.now(UTC).isoformat()

        if data.get('status') == 'healthy':
            logger.info(
                f"Health check passed at {timestamp}. "
                f"All services operational: {data.get('checks', {})}"
            )
        else:
            logger.warning(
                f"Health check degraded at {timestamp}. "
                f"Status: {data.get('status')}. "
                f"Details: {data.get('checks', {})}"
            )

        return {
            'success': True,
            'timestamp': timestamp,
            'status': data.get('status'),
            'checks': data.get('checks', {})
        }

    except requests.Timeout as e:
        logger.error(f'Health check timeout after 45s: {str(e)}')
        raise

    except requests.HTTPError as e:
        logger.error(
            f'Health check HTTP error [{e.response.status_code}]: {str(e)}'
        )
        if e.response.status_code == 503:
            # Service unavailable - log the response details
            try:
                error_data = e.response.json()
                logger.error(f'Service unhealthy details: {error_data}')
            except Exception:
                logger.error(f'Service unhealthy response: {e.response.text}')
        raise

    except requests.RequestException as e:
        logger.error(f'Health check connection failed: {str(e)}')
        raise

    except Exception as e:
        logger.exception(f'Unexpected error during health check: {str(e)}')
        return {
            'success': False,
            'timestamp': datetime.now(UTC).isoformat(),
            'error': str(e)
        }


@shared_task(bind=True)
def celery_worker_health_check(self):
    """
    Simple task to verify Celery worker is processing tasks.
    Can be called periodically to ensure workers are responsive.
    """
    timestamp = datetime.now(UTC).isoformat()
    worker_name = self.request.hostname

    logger.info(f"Celery worker health check passed on {worker_name} at {timestamp}")

    return {
        'success': True,
        'timestamp': timestamp,
        'worker': worker_name,
        'task_id': self.request.id
    }
