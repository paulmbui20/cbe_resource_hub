from datetime import datetime

from django.core.management import BaseCommand
from django.db import transaction

from core.models import Year, Term, AcademicSession

terms: tuple[int, int, int] = (
    1, 2, 3
)


def generate_year():
    current_year = datetime.now().year

    years = [current_year - 1, current_year, current_year + 1]

    return years


class Command(BaseCommand):
    help = "Populate Academic Sessions with Terms and Years"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING("Populating Academic Sessions with Terms and Years..."))

        created_count = 0
        year_found = 0
        db_years = []
        for year in generate_year():
            year, created = Year.objects.get_or_create(
                year=year
            )
            db_years.append(year)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created Academic Year: {year}"))
            else:
                year_found += 1
                self.stdout.write(self.style.NOTICE(f"Found Academic Year: {year}"))

        terms_found = 0
        terms_created = 0
        db_terms = []
        for term in terms:
            term, created = Term.objects.get_or_create(
                term_number=term,
            )
            db_terms.append(term)
            if created:
                terms_created += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {term}"))
            else:
                terms_found += 1
                self.stdout.write(self.style.NOTICE(f"Found: {term}"))

        accademic_session_found = 0
        accademic_session_created = 0
        for year in db_years:
            for term in db_terms:
                accademic_session, created = AcademicSession.objects.get_or_create(
                    current_year=year,
                    current_term=term,
                )
                if created:
                    accademic_session_created += 1
                    self.stdout.write(self.style.SUCCESS(f"Created Academic Session: {accademic_session}"))
                else:
                    accademic_session_found += 1
                    self.stdout.write(self.style.NOTICE(f"Found Academic Session: {accademic_session}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Finished, Created {created_count} year(s), {terms_created} terms and {accademic_session_created} academic session(s) and found {year_found} year(s), {terms_found} term(s) and {accademic_session_found} academic session(s)"
            ))
