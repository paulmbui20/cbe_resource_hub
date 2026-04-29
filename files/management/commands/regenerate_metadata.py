from django.core.management.base import BaseCommand
from files.models import File


class Command(BaseCommand):
    help = 'Regenerate metadata for all files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Only regenerate metadata for specific category (image, video, etc.)',
        )

    def handle(self, *args, **options):
        files = File.objects.all()

        if options['category']:
            files = files.filter(file_category=options['category'])
            self.stdout.write(f"Filtering by category: {options['category']}")

        total = files.count()
        self.stdout.write(f"Regenerating metadata for {total} files...")

        success = 0
        failed = 0

        for i, file_obj in enumerate(files, 1):
            try:
                self.stdout.write(f"[{i}/{total}] Processing: {file_obj.title}")
                file_obj._extract_metadata()
                file_obj.save()
                success += 1
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f"Failed: {file_obj.title} - {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Success: {success}, Failed: {failed}"
            )
        )


