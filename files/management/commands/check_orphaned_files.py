from django.core.management.base import BaseCommand
from files.models import File


class Command(BaseCommand):
    help = 'Check for orphaned file records (files missing from storage)'

    def handle(self, *args, **options):
        files = File.objects.all()
        orphaned = []

        self.stdout.write(f"Checking {files.count()} files...")

        for file_obj in files:
            if not file_obj.file_exists():
                orphaned.append(file_obj)
                self.stdout.write(
                    self.style.WARNING(
                        f"Orphaned: {file_obj.title} (ID: {file_obj.pk})"
                    )
                )

        if orphaned:
            self.stdout.write(
                self.style.ERROR(
                    f"\nFound {len(orphaned)} orphaned file(s)."
                )
            )

            # Ask if user wants to delete orphaned records
            if input("Delete orphaned records? (yes/no): ").lower() == 'yes':
                for file_obj in orphaned:
                    self.stdout.write(f"Deleting {file_obj.title}...")
                    file_obj.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"Deleted {len(orphaned)} orphaned records.")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("No orphaned files found!")
            )
