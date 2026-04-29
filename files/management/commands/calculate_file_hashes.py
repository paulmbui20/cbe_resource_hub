from django.core.management.base import BaseCommand
from files.models import File


class Command(BaseCommand):
    help = 'Calculate file hashes for all files without hashes'

    def handle(self, *args, **options):
        files = File.objects.filter(file_hash='')
        total = files.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("All files already have hashes!"))
            return

        self.stdout.write(f"Calculating hashes for {total} files...")

        success = 0
        failed = 0

        for i, file_obj in enumerate(files, 1):
            try:
                self.stdout.write(f"[{i}/{total}] {file_obj.title}")
                file_obj._calculate_file_hash()
                file_obj.save(update_fields=['file_hash'])
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

