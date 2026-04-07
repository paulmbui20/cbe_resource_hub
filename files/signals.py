from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import File
import logging

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=File)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Delete file from storage when File model is deleted.
    This is a backup to the model's delete() method.
    """
    if instance.file:
        try:
            if instance.file.storage.exists(instance.file.name):
                instance.file.storage.delete(instance.file.name)
                logger.info(f"Deleted file from storage: {instance.file.name}")
        except Exception as e:
            logger.error(f"Failed to delete file {instance.file.name}: {e}")
