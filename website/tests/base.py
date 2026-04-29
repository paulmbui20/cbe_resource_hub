"""
website/tests/base.py

Shared fixtures for all website tests.
"""
from django.test import TestCase

from accounts.models import CustomUser
from core.models import AcademicSession, Term, Year
from resources.models import EducationLevel, Grade, LearningArea, ResourceItem
from website.models import ContactMessage, Partner, EmailSubscriber


def make_pdf(name="web_test.pdf"):
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile(name, b"%PDF-1.4 website test", content_type="application/pdf")


class WebsiteBaseTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = CustomUser.objects.create_superuser(
            email="web_admin@example.com", password="pass123"
        )
        cls.regular_user = CustomUser.objects.create_user(
            email="web_user@example.com", password="pass123"
        )

        # Curriculum chain (needed for ResourceItem and homepage context)
        cls.level = EducationLevel.objects.create(name="Web Level", order=88)
        cls.grade = Grade.objects.create(level=cls.level, name="Web Grade", order=88)
        cls.learning_area = LearningArea.objects.create(name="Web Area")

        cls.year = Year.objects.create(year=2088)
        cls.term = Term.objects.create(term_number=8)
        cls.session = AcademicSession.objects.create(
            current_year=cls.year, current_term=cls.term
        )

        cls.resource = ResourceItem.objects.create(
            title="Website Test Resource",
            description="<p>Web test.</p>",
            grade=cls.grade,
            learning_area=cls.learning_area,
            file=make_pdf(),
            is_free=True,
            resource_type="notes",
        )

        cls.partner = Partner.objects.create(
            name="Test Partner",
            link="https://testpartner.example.com",
        )

        cls.contact_msg = ContactMessage.objects.create(
            name="Test Sender",
            email="sender@example.com",
            subject="Test Subject",
            message="Test message body.",
        )

        cls.subscriber = EmailSubscriber.objects.create(
            email="subscriber@example.com",
            full_name="Test Subscriber",
        )

    def login_as_admin(self):
        self.client.force_login(self.admin)

    def login_as_user(self):
        self.client.force_login(self.regular_user)
