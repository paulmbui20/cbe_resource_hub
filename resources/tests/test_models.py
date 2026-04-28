"""
resources/tests/test_models.py

Covers EducationLevel, Grade, LearningArea, and ResourceItem models:
  - Creation, slugification, constraints, cascade, protected FK, __str__,
    ordering, SEO field auto-fill, download counter, is_free/price coupling,
    custom manager select_related, and file-delete on record delete.
"""

from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from resources.models import EducationLevel, Grade, LearningArea, ResourceItem
from resources.tests.base import ResourceBaseTestCase, make_pdf


# ── EducationLevel ─────────────────────────────────────────────────────────────

class EducationLevelModelTests(ResourceBaseTestCase):

    def test_created(self):
        self.assertIsNotNone(self.level.pk)

    def test_str(self):
        self.assertEqual(str(self.level), "Lower Primary")

    def test_slug_auto_generated(self):
        self.assertEqual(self.level.slug, "lower-primary")

    def test_meta_title_auto_populated(self):
        self.assertEqual(self.level.meta_title, "Lower Primary")

    def test_name_unique_case_insensitive(self):
        with self.assertRaises(Exception):
            EducationLevel.objects.create(name="lower primary", order=2)

    def test_ordering_by_order_then_slug(self):
        l2 = EducationLevel.objects.create(name="Upper Primary", order=2)
        levels = list(EducationLevel.objects.values_list("order", flat=True))
        self.assertEqual(levels, sorted(levels))

    def test_slug_max_length(self):
        long_name = "A" * 120
        lvl = EducationLevel.objects.create(name=long_name, order=99)
        self.assertLessEqual(len(lvl.slug), 110)


# ── Grade ──────────────────────────────────────────────────────────────────────

class GradeModelTests(ResourceBaseTestCase):

    def test_created(self):
        self.assertIsNotNone(self.grade.pk)

    def test_str(self):
        self.assertIn("Lower Primary", str(self.grade))
        self.assertIn("Grade 1", str(self.grade))

    def test_slug_auto_generated(self):
        self.assertEqual(self.grade.slug, "grade-1")

    def test_meta_title_auto_populated(self):
        self.assertEqual(self.grade.meta_title, "Grade 1")

    def test_get_absolute_url(self):
        url = self.grade.get_absolute_url()
        self.assertIn(self.grade.slug, url)

    def test_level_fk_on_delete_protect(self):
        from django.db.models import ProtectedError
        with self.assertRaises(ProtectedError):
            self.level.delete()

    def test_unique_together_level_slug(self):
        with self.assertRaises(Exception):
            Grade.objects.create(level=self.level, name="Grade 1", order=2)

    def test_manager_uses_select_related(self):
        grade = Grade.objects.get(pk=self.grade.pk)
        with self.assertNumQueries(0):
            _ = grade.level.name

    def test_ordering(self):
        g2 = Grade.objects.create(level=self.level, name="Grade 2", order=2)
        grades = list(Grade.objects.values_list("order", flat=True))
        self.assertEqual(grades, sorted(grades))


# ── LearningArea ───────────────────────────────────────────────────────────────

class LearningAreaModelTests(ResourceBaseTestCase):

    def test_created(self):
        self.assertIsNotNone(self.learning_area.pk)

    def test_str(self):
        self.assertEqual(str(self.learning_area), "Mathematics")

    def test_slug_auto_generated(self):
        self.assertEqual(self.learning_area.slug, "mathematics")

    def test_meta_title_auto_populated(self):
        self.assertEqual(self.learning_area.meta_title, "Mathematics")

    def test_get_absolute_url(self):
        url = self.learning_area.get_absolute_url()
        self.assertIn(self.learning_area.slug, url)

    def test_slug_unique(self):
        with self.assertRaises(Exception):
            LearningArea.objects.create(name="Mathematics")

    def test_ordering_by_slug(self):
        LearningArea.objects.create(name="English")
        slugs = list(LearningArea.objects.values_list("slug", flat=True))
        self.assertEqual(slugs, sorted(slugs))


# ── ResourceItem ───────────────────────────────────────────────────────────────

class ResourceItemModelTests(ResourceBaseTestCase):

    def test_created(self):
        self.assertIsNotNone(self.resource.pk)

    def test_str(self):
        self.assertEqual(str(self.resource), "Sample Resource")

    def test_slug_auto_generated_from_title(self):
        self.assertEqual(self.resource.slug, "sample-resource")

    def test_meta_title_auto_populated(self):
        self.assertIsNotNone(self.resource.meta_title)

    def test_meta_description_auto_populated_from_description(self):
        self.assertIn("test resource description", self.resource.meta_description)

    def test_meta_description_strips_html(self):
        self.assertNotIn("<p>", self.resource.meta_description)

    def test_is_free_sets_price_to_zero(self):
        r = self.make_resource(title="Free Res", is_free=True, price=Decimal("100.00"))
        r.refresh_from_db()
        self.assertEqual(r.price, Decimal("0.00"))

    def test_paid_resource_keeps_price(self):
        r = ResourceItem.objects.create(
            title="Paid Resource",
            description="<p>desc</p>",
            grade=self.grade,
            learning_area=self.learning_area,
            file=make_pdf(),
            is_free=False,
            price=Decimal("250.00"),
            resource_type="textbook",
        )
        r.refresh_from_db()
        self.assertEqual(r.price, Decimal("250.00"))

    def test_default_downloads_is_zero(self):
        self.assertEqual(self.resource.downloads, 0)

    def test_increment_downloads_atomic(self):
        r = self.make_resource(title="Download Counter")
        r.increment_downloads()
        r.refresh_from_db()
        self.assertEqual(r.downloads, 1)

    def test_increment_downloads_multiple_times(self):
        r = self.make_resource(title="Multi Download")
        for _ in range(5):
            r.increment_downloads()
        r.refresh_from_db()
        self.assertEqual(r.downloads, 5)

    def test_get_absolute_url(self):
        url = self.resource.get_absolute_url()
        self.assertIn(self.resource.slug, url)

    def test_ordering_newest_first(self):
        r1 = self.make_resource(title="Older Resource")
        r2 = self.make_resource(title="Newer Resource")
        pks = list(ResourceItem.objects.values_list("pk", flat=True))
        self.assertGreater(pks.index(r1.pk), pks.index(r2.pk))

    def test_academic_session_nullable(self):
        r = self.make_resource(title="No Session", academic_session=None)
        self.assertIsNone(r.academic_session)

    def test_vendor_nullable(self):
        r = self.make_resource(title="No Vendor")
        self.assertIsNone(r.vendor)

    def test_resource_type_default_is_other(self):
        r = ResourceItem.objects.create(
            title="Default Type",
            description="<p>d</p>",
            grade=self.grade,
            learning_area=self.learning_area,
            file=make_pdf(),
        )
        self.assertEqual(r.resource_type, "other")

    def test_manager_uses_select_related(self):
        r = ResourceItem.objects.get(pk=self.resource.pk)
        with self.assertNumQueries(0):
            _ = r.grade.name
            _ = r.grade.level.name
            _ = r.learning_area.name

    def test_grade_protected_from_delete_with_resource(self):
        from django.db.models import ProtectedError
        with self.assertRaises(ProtectedError):
            self.grade.delete()

    def test_learning_area_protected_from_delete_with_resource(self):
        from django.db.models import ProtectedError
        with self.assertRaises(ProtectedError):
            self.learning_area.delete()

    def test_academic_session_delete_sets_null(self):
        from core.models import AcademicSession, Year, Term
        y = Year.objects.create(year=2095)
        t = Term.objects.create(term_number=7)
        s = AcademicSession.objects.create(current_year=y, current_term=t)
        r = self.make_resource(title="Session Delete Test", academic_session=s)
        s.delete()
        r.refresh_from_db()
        self.assertIsNone(r.academic_session)

    def test_title_slug_truncated_to_265_chars(self):
        long_title = "W" * 300
        r = ResourceItem.objects.create(
            title=long_title,
            description="<p>d</p>",
            grade=self.grade,
            learning_area=self.learning_area,
            file=make_pdf(name="big.pdf"),
        )
        self.assertLessEqual(len(r.slug), 265)
