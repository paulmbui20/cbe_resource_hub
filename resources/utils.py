import sys
from uuid import uuid4

from django.core.files.storage import storages, FileSystemStorage
from django.utils.text import slugify


def get_year_and_month_from_created_at_datetime(created_at):
    year = created_at.year
    month = created_at.month

    return year, month


def file_upload_path(instance, filename):
    """
    Generate file path for uploads preventing collisions.
    """

    extension = filename.split('.')[-1] if '.' in filename else ''

    safe_filename = slugify(instance.title or "resource item file")[:275] or 'untitled-resource'

    filename = f'{safe_filename}-{uuid4()}.{extension}' if extension else f"{safe_filename} - {uuid4()}"

    year, month = get_year_and_month_from_created_at_datetime(instance.created_at)

    resource_type = instance.resource_type if getattr(instance, 'resource_type', None) else None
    grade = instance.grade if getattr(instance, 'grade', None) else None
    if resource_type and grade:
        resource_type = slugify(resource_type)
        grade = slugify(grade)
        filename = f'resources/{grade}/{resource_type}/{year}/{month}/{filename}'

    return filename


class PublicFilesStorageCallable:

    def __call__(self):

        # In tests, always use FileSystemStorage
        if "pytest" in sys.modules or "test" in sys.argv:
            return FileSystemStorage()

        try:
            return storages['public_files']
        except:
            return storages["default"]
