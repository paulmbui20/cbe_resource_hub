"""
seo/tests/base.py

Shared fixtures and helpers for all SEO tests.
We need concrete models to exercise the abstract SEOModel and SlugRedirectMixin.
We use the real ResourceItem as a concrete host for SlugRedirectMixin.
"""

from django.test import TestCase

from accounts.models import CustomUser
from core.models import AcademicSession, Term, Year
from resources.models import EducationLevel, Grade, LearningArea, ResourceItem
from seo.models import SlugRedirect


def make_pdf(name="seo_test.pdf"):
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile(name, b"%PDF-1.4 seo test", content_type="application/pdf")


class SEOBaseTestCase(TestCase):
    """Common DB state shared by all SEO test cases."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = CustomUser.objects.create_superuser(
            email="seo_admin@example.com", password="pass123"
        )
        cls.regular_user = CustomUser.objects.create_user(
            email="seo_user@example.com", password="pass123"
        )

        # Curriculum chain needed for ResourceItem
        cls.level = EducationLevel.objects.create(name="SEO Level", order=99)
        cls.grade = Grade.objects.create(level=cls.level, name="SEO Grade", order=99)
        cls.learning_area = LearningArea.objects.create(name="SEO Subject")

        cls.year = Year.objects.create(year=2099)
        cls.term = Term.objects.create(term_number=9)
        cls.session = AcademicSession.objects.create(
            current_year=cls.year, current_term=cls.term
        )

        cls.resource = ResourceItem.objects.create(
            title="SEO Resource",
            description="<p>SEO test resource.</p>",
            grade=cls.grade,
            learning_area=cls.learning_area,
            file=make_pdf(),
            is_free=True,
            resource_type="notes",
        )

    def login_as_admin(self):
        self.client.force_login(self.admin)

    def login_as_user(self):
        self.client.force_login(self.regular_user)

    @classmethod
    def make_redirect(cls, old_slug="old-slug", new_slug="new-slug"):
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(ResourceItem)
        return SlugRedirect.objects.create(
            content_type=ct,
            object_id=cls.resource.pk,
            old_slug=old_slug,
            new_slug=new_slug,
        )
