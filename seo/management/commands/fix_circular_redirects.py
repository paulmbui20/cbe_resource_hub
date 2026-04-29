# seo/management/commands/fix_circular_redirects.py

from django.core.cache import cache
from django.core.management.base import BaseCommand

from seo.models import SlugRedirect


class Command(BaseCommand):
    help = 'Find and fix circular redirects in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without actually fixing',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear all redirect caches after fixing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear_cache = options['clear_cache']

        self.stdout.write(self.style.WARNING("\nScanning for circular redirects...\n"))

        # Get all redirects
        all_redirects = list(SlugRedirect.objects.all())
        circular_pairs = []
        fixed_count = 0

        # Check for circular redirects
        for r1 in all_redirects:
            # Find if there's a reverse redirect
            r2 = SlugRedirect.objects.filter(
                old_slug=r1.new_slug,
                new_slug=r1.old_slug
            ).first()

            if r2:
                # Circular redirect found
                pair = tuple(sorted([r1.id, r2.id]))
                if pair not in circular_pairs:
                    circular_pairs.append(pair)

                    self.stdout.write(
                        self.style.ERROR(
                            f"\n✗ Circular redirect found:"
                        )
                    )
                    self.stdout.write(f"  ID {r1.id}: {r1.old_slug} → {r1.new_slug}")
                    self.stdout.write(f"  ID {r2.id}: {r2.old_slug} → {r2.new_slug}")

                    if not dry_run:
                        # Delete both redirects
                        cache.delete(f'slug_redirect_{r1.old_slug}')
                        cache.delete(f'slug_redirect_{r2.old_slug}')
                        r1.delete()
                        r2.delete()
                        fixed_count += 2
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Deleted both redirects"
                            )
                        )

        # Check for redirect chains (A → B → C)
        self.stdout.write(self.style.WARNING("\n\nScanning for redirect chains...\n"))

        chain_count = 0
        for redirect in all_redirects:
            # Check if new_slug points to another redirect
            next_redirect = SlugRedirect.objects.filter(
                old_slug=redirect.new_slug
            ).first()

            if next_redirect:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠ Redirect chain found:"
                    )
                )
                self.stdout.write(f"  {redirect.old_slug} → {redirect.new_slug} → {next_redirect.new_slug}")

                if not dry_run:
                    # Update redirect to point to final destination
                    redirect.new_slug = next_redirect.new_slug
                    redirect.save()
                    cache.delete(f'slug_redirect_{redirect.old_slug}')
                    chain_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Fixed to: {redirect.old_slug} → {redirect.new_slug}"
                        )
                    )

        # Summary
        self.stdout.write(f"\n{'=' * 60}")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDRY RUN - No changes made"
                )
            )
            self.stdout.write(f"Would delete {fixed_count} circular redirects")
            self.stdout.write(f"Would fix {chain_count} redirect chains")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nFixed {fixed_count} circular redirects"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Fixed {chain_count} redirect chains"
                )
            )

        # Clear all redirect caches if requested
        if clear_cache and not dry_run:
            self.stdout.write(self.style.WARNING("\nClearing all redirect caches..."))

            # Get all redirect cache keys
            all_slugs = set()
            for r in SlugRedirect.objects.all():
                all_slugs.add(r.old_slug)
                all_slugs.add(r.new_slug)

            cache_keys = [f'slug_redirect_{slug}' for slug in all_slugs]
            cache.delete_many(cache_keys)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Cleared {len(cache_keys)} redirect cache keys"
                )
            )

        self.stdout.write(f"{'=' * 60}\n")

# Usage:
# python manage.py fix_circular_redirects --dry-run
# python manage.py fix_circular_redirects
# python manage.py fix_circular_redirects --clear-cache
