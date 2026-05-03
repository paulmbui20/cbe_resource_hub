"""
website/tests/test_models.py

Tests for ContactMessage, Partner, and EmailSubscriber models:
  - Creation, __str__, field defaults, ordering
  - ContactMessage: is_read defaults False, ordering newest-first
  - Partner: slug auto-generated from name, meta_title auto-filled,
    meta_description stripped from HTML description, unique constraints
  - EmailSubscriber: email unique, opted_out defaults False, __str__
"""

from website.models import ContactMessage, Partner, EmailSubscriber, FAQ, Testimonial
from website.tests.base import WebsiteBaseTestCase


# ── ContactMessage ─────────────────────────────────────────────────────────────


class ContactMessageModelTests(WebsiteBaseTestCase):
    def test_created(self):
        self.assertIsNotNone(self.contact_msg.pk)

    def test_str_contains_name(self):
        self.assertIn("Test Sender", str(self.contact_msg))

    def test_str_contains_subject(self):
        self.assertIn("Test Subject", str(self.contact_msg))

    def test_str_unread_shows_bullet(self):
        self.assertIn("●", str(self.contact_msg))

    def test_str_read_shows_checkmark(self):
        msg = ContactMessage.objects.create(
            name="Read Sender", subject="Read Sub", message="Body", is_read=True
        )
        self.assertIn("✓", str(msg))

    def test_is_read_defaults_false(self):
        msg = ContactMessage.objects.create(
            name="New Sender", subject="New Sub", message="Body"
        )
        self.assertFalse(msg.is_read)

    def test_email_optional(self):
        msg = ContactMessage.objects.create(
            name="No Email", subject="Sub", message="Body"
        )
        self.assertIsNone(msg.email)

    def test_phone_optional(self):
        msg = ContactMessage.objects.create(
            name="No Phone", subject="Sub", message="Body"
        )
        self.assertIsNone(msg.phone)

    def test_ordering_newest_first(self):
        m1 = ContactMessage.objects.create(name="Old", subject="A", message="M")
        m2 = ContactMessage.objects.create(name="New", subject="B", message="M")
        messages = list(ContactMessage.objects.values_list("pk", flat=True))
        self.assertGreater(messages.index(m1.pk), messages.index(m2.pk))


# ── Partner ────────────────────────────────────────────────────────────────────


class PartnerModelTests(WebsiteBaseTestCase):
    def test_created(self):
        self.assertIsNotNone(self.partner.pk)

    def test_str_contains_name(self):
        self.assertIn("Test Partner", str(self.partner))

    def test_str_contains_link_when_set(self):
        self.assertIn("testpartner.example.com", str(self.partner))

    def test_str_without_link(self):
        p = Partner.objects.create(name="No Link Partner")
        self.assertIn("No Link Partner", str(p))

    def test_slug_auto_generated(self):
        self.assertEqual(self.partner.slug, "test-partner")

    def test_meta_title_auto_populated(self):
        self.assertEqual(self.partner.meta_title, "Test Partner")

    def test_meta_description_stripped_from_html(self):
        p = Partner.objects.create(
            name="HTML Desc Partner",
            description="<p>Clean description here.</p>",
        )
        self.assertNotIn("<p>", p.meta_description)
        self.assertIn("Clean description here", p.meta_description)

    def test_show_as_banner_defaults_false(self):
        p = Partner.objects.create(name="Banner Default Partner")
        self.assertFalse(p.show_as_banner)

    def test_banner_cta_default(self):
        p = Partner.objects.create(name="CTA Default Partner")
        self.assertEqual(p.banner_cta, "Learn More")

    def test_name_unique_constraint(self):
        with self.assertRaises(Exception):
            # Same name case-insensitively
            Partner.objects.create(name="test partner")

    def test_link_unique_constraint(self):
        with self.assertRaises(Exception):
            Partner.objects.create(
                name="Duplicate Link Partner",
                link="https://testpartner.example.com",
            )

    def test_link_nullable(self):
        p = Partner.objects.create(name="No URL Partner")
        self.assertIsNone(p.link)

    def test_ordering_newest_first(self):
        p1 = Partner.objects.create(name="Old Partner")
        p2 = Partner.objects.create(name="New Partner")
        pks = list(Partner.objects.values_list("pk", flat=True))
        self.assertGreater(pks.index(p1.pk), pks.index(p2.pk))


# ── EmailSubscriber ────────────────────────────────────────────────────────────


class EmailSubscriberModelTests(WebsiteBaseTestCase):
    def test_created(self):
        self.assertIsNotNone(self.subscriber.pk)

    def test_str_returns_email(self):
        self.assertEqual(str(self.subscriber), "subscriber@example.com")

    def test_opted_out_defaults_false(self):
        sub = EmailSubscriber.objects.create(email="fresh@example.com")
        self.assertFalse(sub.opted_out)

    def test_full_name_optional(self):
        sub = EmailSubscriber.objects.create(email="nofullname@example.com")
        self.assertEqual(sub.full_name, "")

    def test_email_unique(self):
        with self.assertRaises(Exception):
            EmailSubscriber.objects.create(email="subscriber@example.com")

    def test_ordering_newest_first(self):
        s1 = EmailSubscriber.objects.create(email="old_sub@example.com")
        s2 = EmailSubscriber.objects.create(email="new_sub@example.com")
        pks = list(EmailSubscriber.objects.values_list("pk", flat=True))
        self.assertGreater(pks.index(s1.pk), pks.index(s2.pk))


# ── FAQ ────────────────────────────────────────────────────────────────────────


class FAQModelTests(WebsiteBaseTestCase):
    def test_created(self):
        faq = FAQ.objects.create(question="Q?", answer="A")
        self.assertIsNotNone(faq.pk)

    def test_str_returns_truncated_question(self):

        long_q = "A" * 100
        faq = FAQ.objects.create(question=long_q, answer="A")
        self.assertEqual(str(faq), long_q[:80])

    def test_defaults(self):

        faq = FAQ.objects.create(question="Q?", answer="A")
        self.assertTrue(faq.is_active)
        self.assertEqual(faq.order, 0)

    def test_ordering(self):

        faq1 = FAQ.objects.create(question="Q1?", answer="A", order=1)
        faq2 = FAQ.objects.create(question="Q2?", answer="A", order=0)
        # Should be ordered by -created_at, order
        pks = list(FAQ.objects.values_list("pk", flat=True))
        self.assertEqual(pks[0], faq2.pk)
        self.assertEqual(pks[1], faq1.pk)


# ── Testimonial ────────────────────────────────────────────────────────────────


class TestimonialModelTests(WebsiteBaseTestCase):
    def test_created(self):

        t = Testimonial.objects.create(author_name="A", body="B")
        self.assertIsNotNone(t.pk)

    def test_str_format(self):

        t = Testimonial.objects.create(author_name="John Doe", body="Great!", rating=4)
        self.assertEqual(str(t), "John Doe — 4★")

    def test_defaults(self):

        t = Testimonial.objects.create(author_name="A", body="B")
        self.assertEqual(t.rating, 5)
        self.assertFalse(t.is_featured)
        self.assertTrue(t.is_active)
        self.assertEqual(t.order, 0)
        self.assertEqual(t.author_role, "")
        self.assertEqual(t.author_organization, "")

    def test_ordering(self):

        t1 = Testimonial.objects.create(author_name="A1", body="B", order=2)
        t2 = Testimonial.objects.create(author_name="A2", body="B", order=1)
        pks = list(Testimonial.objects.values_list("pk", flat=True))
        self.assertEqual(pks[0], t2.pk)
        self.assertEqual(pks[1], t1.pk)
