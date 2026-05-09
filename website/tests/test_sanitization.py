from django.test import TestCase
from website.models import Partner
from resources.models import ResourceItem, Grade, LearningArea, EducationLevel
from cms.models import Page
from core.models import AcademicSession, Year, Term
from accounts.models import CustomUser

class SanitizationTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="testuser@example.com",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        self.year = Year.objects.create(year=2026)
        self.term = Term.objects.create(term_number=1)
        self.session = AcademicSession.objects.create(
            current_year=self.year,
            current_term=self.term
        )
        self.level = EducationLevel.objects.create(name="Primary", slug="primary")
        self.grade = Grade.objects.create(level=self.level, name="Grade 1", slug="grade-1")
        self.la = LearningArea.objects.create(name="Math", slug="math")

    def test_partner_description_sanitization(self):
        """Test that Partner description is sanitized on save."""
        p = Partner.objects.create(
            name="Secure Partner",
            description="<script>alert('xss')</script><b>Bold Content</b><iframe src='http://malicious.com'></iframe>"
        )
        # script and iframe should be gone, content of script should be gone if NH3_CLEAN_CONTENT_TAGS has it
        assert "<script>" not in p.description
        assert "alert('xss')" not in p.description
        assert "<iframe>" not in p.description
        assert "<b>Bold Content</b>" in p.description

    def test_resource_item_description_sanitization(self):
        """Test that ResourceItem description is sanitized on save."""
        r = ResourceItem.objects.create(
            title="Secure Resource",
            description="<img src='valid.jpg' onerror='alert(1)'><i>Safe Italic</i>",
            vendor=self.user,
            academic_session=self.session,
            grade=self.grade,
            learning_area=self.la
        )
        assert "onerror" not in r.description
        assert "alert(1)" not in r.description
        assert '<img src="valid.jpg">' in r.description
        assert "<i>Safe Italic</i>" in r.description

    def test_page_content_sanitization(self):
        """Test that Page content is sanitized on save."""
        pg = Page.objects.create(
            title="Secure Page",
            content="<div onclick='doEvil()'>Content</div><style>body { background: red; }</style><u>Underlined</u>"
        )
        assert "onclick" not in pg.content
        assert "doEvil()" not in pg.content
        assert "<style>" not in pg.content
        assert "background: red" not in pg.content
        assert "<div>Content</div>" in pg.content
        assert "<u>Underlined</u>" in pg.content

    def test_safe_html_is_preserved(self):
        """Confirm that common safe HTML tags and attributes are preserved."""
        safe_html = (
            "<h1>Title</h1>"
            "<p>Paragraph with <a href='https://example.com' target='_blank'>link</a>.</p>"
            "<ul><li>Item 1</li><li>Item 2</li></ul>"
            "<table><tr><td>Cell</td></tr></table>"
        )
        p = Partner.objects.create(name="Safe Partner", description=safe_html)
        
        # Check some key elements
        assert "<h1>Title</h1>" in p.description
        assert "href=\"https://example.com\"" in p.description
        assert "target=\"_blank\"" in p.description
        assert "<ul>" in p.description
        assert "<li>Item 1</li>" in p.description
        assert "<table>" in p.description

    def test_rel_attributes_added_to_links(self):
        """If NH3_LINK_REL is set, it should add rel attributes to links."""
        p = Partner.objects.create(
            name="Link Partner",
            description="<a href='https://external.com'>External Link</a>"
        )
        # Depending on NH3_LINK_REL setting in base.py
        # Current setting: NH3_LINK_REL = "noopener noreferrer nofollow"
        assert 'rel="noopener noreferrer nofollow"' in p.description
