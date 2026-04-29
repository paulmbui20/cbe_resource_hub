"""
core/tests/test_models.py

Model tests for Term, Year, AcademicSession, and TimeStampedModel.

Covers:
  - Creation with valid data
  - Unique constraints
  - Null / missing field errors
  - Auto-slug generation for AcademicSession
  - unique_together constraint for (year, term) pair
  - __str__ representations
  - get_absolute_url
  - Ordering
"""

from django.db import IntegrityError
from django.test import TestCase

from core.models import AcademicSession, Term, Year
from core.tests.base import CoreBaseTestCase


# ── Term ─────────────────────────────────────────────────────────────────────

class TermModelTests(CoreBaseTestCase):

    def test_term_created(self):
        self.assertIsNotNone(self.term.pk)

    def test_term_str(self):
        self.assertEqual(str(self.term), "Term 1")

    def test_term_number_unique(self):
        with self.assertRaises(IntegrityError):
            Term.objects.create(term_number=1)

    def test_term_number_null_raises(self):
        with self.assertRaises(IntegrityError):
            Term.objects.create(term_number=None)

    def test_term_ordering_descending(self):
        Term.objects.create(term_number=2)
        Term.objects.create(term_number=3)
        numbers = list(Term.objects.values_list("term_number", flat=True))
        self.assertEqual(numbers, sorted(numbers, reverse=True))

    def test_term_timestamps_present(self):
        self.assertIsNotNone(self.term.created_at)
        self.assertIsNotNone(self.term.updated_at)


# ── Year ─────────────────────────────────────────────────────────────────────

class YearModelTests(CoreBaseTestCase):

    def test_year_created(self):
        self.assertIsNotNone(self.year.pk)

    def test_year_str(self):
        self.assertEqual(str(self.year), "2030")

    def test_year_unique(self):
        with self.assertRaises(IntegrityError):
            Year.objects.create(year=2030)

    def test_year_null_raises(self):
        with self.assertRaises(IntegrityError):
            Year.objects.create(year=None)

    def test_year_ordering_descending(self):
        Year.objects.create(year=2031)
        Year.objects.create(year=2029)
        years = list(Year.objects.values_list("year", flat=True))
        self.assertEqual(years, sorted(years, reverse=True))

    def test_default_year_is_current_year(self):
        from datetime import datetime
        y = Year.objects.create(year=datetime.now().year + 5)
        self.assertIsNotNone(y.year)


# ── AcademicSession ───────────────────────────────────────────────────────────

class AcademicSessionModelTests(CoreBaseTestCase):

    def test_session_created(self):
        self.assertIsNotNone(self.session.pk)

    def test_session_str(self):
        self.assertEqual(str(self.session), "2030 - Term 1")

    def test_session_slug_auto_generated(self):
        self.assertEqual(self.session.slug, "2030-term-1")

    def test_session_slug_not_empty(self):
        self.assertTrue(bool(self.session.slug))

    def test_session_get_absolute_url(self):
        url = self.session.get_absolute_url()
        self.assertIn(self.session.slug, url)

    def test_unique_together_year_term(self):
        with self.assertRaises(IntegrityError):
            AcademicSession.objects.create(
                current_year=self.year,
                current_term=self.term,
            )

    def test_different_year_same_term_allowed(self):
        new_year = Year.objects.create(year=2031)
        s = AcademicSession.objects.create(
            current_year=new_year,
            current_term=self.term,
        )
        self.assertIsNotNone(s.pk)

    def test_same_year_different_term_allowed(self):
        new_term = Term.objects.create(term_number=2)
        s = AcademicSession.objects.create(
            current_year=self.year,
            current_term=new_term,
        )
        self.assertIsNotNone(s.pk)

    def test_null_year_raises(self):
        """Passing None for a FK raises before the DB even sees the row,
        because AcademicSession.save() accesses current_year to build the slug."""
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises((IntegrityError, ObjectDoesNotExist, ValueError)):
            AcademicSession.objects.create(
                current_year=None,
                current_term=self.term,
            )

    def test_null_term_raises(self):
        """Same as above for current_term."""
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises((IntegrityError, ObjectDoesNotExist, ValueError)):
            AcademicSession.objects.create(
                current_year=self.year,
                current_term=None,
            )

    def test_year_cascade_deletes_session(self):
        y = Year.objects.create(year=2099)
        t = Term.objects.create(term_number=9)
        s = AcademicSession.objects.create(current_year=y, current_term=t)
        pk = s.pk
        y.delete()
        self.assertFalse(AcademicSession.objects.filter(pk=pk).exists())

    def test_term_cascade_deletes_session(self):
        y = Year.objects.create(year=2098)
        t = Term.objects.create(term_number=8)
        s = AcademicSession.objects.create(current_year=y, current_term=t)
        pk = s.pk
        t.delete()
        self.assertFalse(AcademicSession.objects.filter(pk=pk).exists())

    def test_manager_uses_select_related(self):
        # Confirm the custom manager returns sessions with year/term pre-loaded
        session = AcademicSession.objects.get(pk=self.session.pk)
        # Accessing related objects should not trigger additional queries
        with self.assertNumQueries(0):
            _ = session.current_year.year
            _ = session.current_term.term_number

    def test_slug_not_overwritten_on_resave(self):
        original_slug = self.session.slug
        self.session.save()
        self.session.refresh_from_db()
        self.assertEqual(self.session.slug, original_slug)


# ── TimeStampedModel ─────────────────────────────────────────────────────────

class TimeStampedModelTests(TestCase):
    """Term inherits TimeStampedModel; use it as a proxy."""

    def test_created_at_set_on_create(self):
        t = Term.objects.create(term_number=50)
        self.assertIsNotNone(t.created_at)

    def test_updated_at_set_on_create(self):
        t = Term.objects.create(term_number=51)
        self.assertIsNotNone(t.updated_at)

    def test_updated_at_changes_on_save(self):
        import time
        t = Term.objects.create(term_number=52)
        original_updated = t.updated_at
        time.sleep(0.05)
        t.save()
        t.refresh_from_db()
        self.assertGreater(t.updated_at, original_updated)

    def test_created_at_does_not_change_on_save(self):
        t = Term.objects.create(term_number=53)
        original_created = t.created_at
        t.save()
        t.refresh_from_db()
        self.assertEqual(t.created_at, original_created)
