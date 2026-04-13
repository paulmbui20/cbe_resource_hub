"""
resources/management/commands/populate_menus.py

Idempotent command to seed the Primary Header and Footer menus with:
  - Primary Header:
      Home  |  Resources  |  Categories ▾  (dropdown of all resource types)
  - Footer:
      Quick Links (same top-level items + nested Categories)
      Contact  (from site settings)

Run:  python manage.py populate_menus
Re-running is safe (uses get_or_create throughout).
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse

from cms.models import Menu, MenuItem
from resources.models import ResourceItem


RESOURCE_TYPES = [
    (key, label)
    for key, label in ResourceItem._meta.get_field("resource_type").choices
]

# Top-level items that appear in both menus.
# Each tuple: (title, url, order)
PRIMARY_ITEMS = [
    ("Home", "/", 0),
    ("Resources", "/resources/", 10),
    ("Contact", "/contact/", 30),
]

# Items added only to the footer Quick Links column.
FOOTER_ONLY_ITEMS: list[tuple[str, str, int]] = []


class Command(BaseCommand):
    help = "Idempotently seed Primary Header and Footer menus."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("➜  Seeding menus…"))

        # ── 1. Ensure menus exist ──────────────────────────────────────────
        header_menu, _ = Menu.objects.get_or_create(name="Primary Header")
        footer_menu, _ = Menu.objects.get_or_create(name="Footer")

        # ── 2. Top-level items for header ──────────────────────────────────
        for title, url, order in PRIMARY_ITEMS:
            MenuItem.objects.get_or_create(
                menu=header_menu,
                parent=None,
                title=title,
                defaults={"url": url, "order": order},
            )

        # ── 3. "Categories" parent + resource-type children (header) ──────
        categories_header, _ = MenuItem.objects.get_or_create(
            menu=header_menu,
            parent=None,
            title="Categories",
            defaults={"url": "#", "order": 20},
        )
        for order, (key, label) in enumerate(RESOURCE_TYPES):
            url = reverse("resources:type_detail", kwargs={"resource_type": key})
            MenuItem.objects.get_or_create(
                menu=header_menu,
                parent=categories_header,
                title=label,
                defaults={"url": url, "order": order},
            )

        # ── 4. Top-level quick links for footer ────────────────────────────
        for title, url, order in PRIMARY_ITEMS + FOOTER_ONLY_ITEMS:
            MenuItem.objects.get_or_create(
                menu=footer_menu,
                parent=None,
                title=title,
                defaults={"url": url, "order": order},
            )

        # ── 5. "Categories" parent + resource-type children (footer) ──────
        categories_footer, _ = MenuItem.objects.get_or_create(
            menu=footer_menu,
            parent=None,
            title="Categories",
            defaults={"url": "#", "order": 20},
        )
        for order, (key, label) in enumerate(RESOURCE_TYPES):
            url = reverse("resources:type_detail", kwargs={"resource_type": key})
            MenuItem.objects.get_or_create(
                menu=footer_menu,
                parent=categories_footer,
                title=label,
                defaults={"url": url, "order": order},
            )

        # ── Summary ───────────────────────────────────────────────────────
        h_count = MenuItem.objects.filter(menu=header_menu).count()
        f_count = MenuItem.objects.filter(menu=footer_menu).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"✔  Primary Header: {h_count} items   |   Footer: {f_count} items"
            )
        )
