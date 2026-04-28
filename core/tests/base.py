"""
core/tests/base.py

Shared fixtures for all core app tests.
Creates one Year, one Term, and one AcademicSession that every
test class can reference via cls.year / cls.term / cls.session.
Also creates admin, regular user, and vendor accounts.
"""

from django.test import TestCase

from accounts.models import CustomUser
from core.models import AcademicSession, Term, Year


class CoreBaseTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.year = Year.objects.create(year=2030)
        cls.term = Term.objects.create(term_number=1)
        cls.session = AcademicSession.objects.create(
            current_year=cls.year,
            current_term=cls.term,
        )
        cls.admin = CustomUser.objects.create_superuser(
            email="core_admin@example.com", password="pass123"
        )
        cls.regular_user = CustomUser.objects.create_user(
            email="core_user@example.com", password="pass123"
        )
        cls.vendor = CustomUser.objects.create_user(
            email="core_vendor@example.com",
            password="pass123",
            role=CustomUser.Role.VENDOR,
            is_vendor=True,
        )

    def login_as_admin(self):
        self.client.force_login(self.admin)

    def login_as_user(self):
        self.client.force_login(self.regular_user)

    def login_as_vendor(self):
        self.client.force_login(self.vendor)
