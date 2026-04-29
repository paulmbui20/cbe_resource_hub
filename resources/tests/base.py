"""
resources/tests/base.py

Shared fixtures for all resources app tests.
Creates the full dependency chain needed for ResourceItem:
  EducationLevel → Grade → LearningArea → (AcademicSession) → ResourceItem
"""

import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import CustomUser
from core.models import AcademicSession, Term, Year
from resources.models import EducationLevel, Grade, LearningArea, ResourceItem


def make_pdf(name="test.pdf"):
    """Return a minimal fake PDF file for uploads."""
    return SimpleUploadedFile(name, b"%PDF-1.4 fake pdf content", content_type="application/pdf")


class ResourceBaseTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # User hierarchy
        cls.admin = CustomUser.objects.create_superuser(
            email="res_admin@example.com", password="pass123"
        )
        cls.vendor = CustomUser.objects.create_user(
            email="res_vendor@example.com",
            password="pass123",
            role=CustomUser.Role.VENDOR,
            is_vendor=True,
        )
        cls.regular_user = CustomUser.objects.create_user(
            email="res_user@example.com", password="pass123"
        )

        # Curriculum hierarchy
        cls.level = EducationLevel.objects.create(name="Lower Primary", order=1)
        cls.grade = Grade.objects.create(level=cls.level, name="Grade 1", order=1)
        cls.learning_area = LearningArea.objects.create(name="Mathematics")

        # Academic session
        cls.year = Year.objects.create(year=2030)
        cls.term = Term.objects.create(term_number=1)
        cls.session = AcademicSession.objects.create(
            current_year=cls.year, current_term=cls.term
        )

        # One published resource
        cls.resource = ResourceItem.objects.create(
            title="Sample Resource",
            description="<p>A test resource description.</p>",
            grade=cls.grade,
            learning_area=cls.learning_area,
            academic_session=cls.session,
            file=make_pdf(),
            is_free=True,
            resource_type="notes",
        )

    def login_as_admin(self):
        self.client.force_login(self.admin)

    def login_as_vendor(self):
        self.client.force_login(self.vendor)

    def login_as_user(self):
        self.client.force_login(self.regular_user)

    @classmethod
    def make_resource(cls, title="Extra Resource", **kwargs):
        defaults = dict(
            description="<p>content</p>",
            grade=cls.grade,
            learning_area=cls.learning_area,
            file=make_pdf(),
            is_free=True,
            resource_type="notes",
        )
        defaults.update(kwargs)
        return ResourceItem.objects.create(title=title, **defaults)
