"""
cms/management/commands/populate_site_settings.py

Idempotent command to seed some important SiteSetting:
   Structure ->  ('key', 'value')

   Sample List:
      [
          ("site_name", "................"),
          ("contact_phone", f"{settings.CONTACT_PHONE}"),
          ("contact_email", f"{settings.CONTACT_EMAIL}"),
          ("google_oauth_client_id", f"{settings.GOOGLE_OAUTH_CLIENT_ID}"),
          ("site_indexing", "true"),
          ("meta_description", "................"),
      ]

Run:  `python manage.py populate_site_settings`
Re-running is safe (uses get_or_create throughout).
"""
from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction

from cms.models import SiteSetting

SITE_SETTINGS_LIST: list[tuple[str, str]] = [

    ("site_name", "CBE Resources Hub"),
    ("contact_phone", f"{settings.CONTACT_PHONE}"),
    ("contact_email", f"{settings.CONTACT_EMAIL}"),
    ("google_oauth_client_id", f"{settings.GOOGLE_OAUTH_CLIENT_ID}"),
    ("site_indexing", "true"),
    ("meta_description",
     "A free platform to access CBC / CBE resources that are up-to-date like notes, schemes of work, lesson plans, past papers, exams, holiday assignments, setbook guides and more, for all learning areas across all levels from pre-primary to senior secondary school."
     ),
]


class Command(BaseCommand):
    help = "Populate Site Settings"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("➜ Populating Site Settings..."))

        created_count = 0
        settings_found = 0
        for key, value in SITE_SETTINGS_LIST:
            setting, created = SiteSetting.objects.get_or_create(
                key=key,
                defaults={"value": value}
            )
            if created:
                created_count += 1
            else:
                settings_found += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Finished, created {created_count} Site Setting(s), found {settings_found} existing Site Setting(s)"
            )
        )
