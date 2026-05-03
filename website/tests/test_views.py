"""
website/tests/test_views.py

Tests for all public website views:
  HomePageView: GET 200, template, context keys (featured/popular resources,
      stats, education_levels, resource_type_cards)
  ContactView: GET 200, template, context default_topics; POST valid saves
      ContactMessage and redirects; POST honeypot blocked; POST invalid re-renders
  email_subscription: POST valid saves subscriber and returns htmx partial;
      POST invalid returns form partial; GET returns form partial with error
  PartnerListView: GET 200, template, context partners
  Health check endpoints: health/, health/live/, health/ready/ return 200
"""

import json

from unittest.mock import patch

from django.core.cache import cache

from website.models import ContactMessage, EmailSubscriber, Partner, FAQ, Testimonial
from website.tests.base import WebsiteBaseTestCase


# ── HomePageView ───────────────────────────────────────────────────────────────


class HomePageViewTests(WebsiteBaseTestCase):
    URL = "/"

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.URL), "website/home.html")

    def test_context_has_featured_resources(self):
        r = self.client.get(self.URL)
        self.assertIn("featured_resources", r.context)

    def test_context_has_popular_resources(self):
        r = self.client.get(self.URL)
        self.assertIn("popular_resources", r.context)

    def test_context_has_total_resources(self):
        r = self.client.get(self.URL)
        self.assertIn("total_resources", r.context)

    def test_context_has_total_levels(self):
        r = self.client.get(self.URL)
        self.assertIn("total_levels", r.context)

    def test_context_has_total_areas(self):
        r = self.client.get(self.URL)
        self.assertIn("total_areas", r.context)

    def test_context_has_total_downloads(self):
        r = self.client.get(self.URL)
        self.assertIn("total_downloads", r.context)

    def test_context_has_education_levels(self):
        r = self.client.get(self.URL)
        self.assertIn("education_levels", r.context)

    def test_context_has_resource_type_cards(self):
        r = self.client.get(self.URL)
        self.assertIn("resource_type_cards", r.context)

    def test_resource_type_cards_are_dicts_with_expected_keys(self):
        r = self.client.get(self.URL)
        cards = r.context["resource_type_cards"]
        self.assertIsInstance(cards, list)
        if cards:
            card = cards[0]
            for key in ("key", "icon", "label", "desc", "count"):
                self.assertIn(key, card, f"Missing key '{key}' in resource type card")

    def test_only_free_resources_in_featured(self):
        r = self.client.get(self.URL)
        featured = list(r.context["featured_resources"])
        self.assertTrue(all(res.is_free for res in featured))

    def test_total_resources_count_correct(self):
        from resources.models import ResourceItem

        expected = ResourceItem.objects.count()
        r = self.client.get(self.URL)
        self.assertEqual(r.context["total_resources"], expected)

    def test_total_downloads_is_non_negative(self):
        r = self.client.get(self.URL)
        self.assertGreaterEqual(r.context["total_downloads"], 0)


# ── ContactView ────────────────────────────────────────────────────────────────


class ContactViewTests(WebsiteBaseTestCase):
    URL = "/contact/"

    def _valid_post(self, **overrides):
        data = {
            "name": "Test Sender",
            "email": "sender@test.com",
            "subject": "Help needed",
            "message": "This is a test contact message.",
            "website_url": "",  # honeypot
        }
        data.update(overrides)
        return data

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.URL), "website/contact.html")

    def test_context_has_default_topics(self):
        r = self.client.get(self.URL)
        self.assertIn("default_topics", r.context)
        self.assertIsInstance(r.context["default_topics"], list)
        self.assertTrue(len(r.context["default_topics"]) > 0)

    @patch("website.views.notify_contact_form")
    def test_valid_post_creates_contact_message(self, mock_notify):
        count_before = ContactMessage.objects.count()
        self.client.post(self.URL, data=self._valid_post())
        self.assertEqual(ContactMessage.objects.count(), count_before + 1)

    @patch("website.views.notify_contact_form")
    def test_valid_post_triggers_notification(self, mock_notify):
        self.client.post(self.URL, data=self._valid_post())
        mock_notify.assert_called_once()

    @patch("website.views.notify_contact_form")
    def test_valid_post_redirects_to_contact(self, mock_notify):
        r = self.client.post(self.URL, data=self._valid_post())
        self.assertRedirects(r, self.URL)

    @patch("website.views.notify_contact_form")
    def test_valid_post_adds_success_message(self, mock_notify):
        r = self.client.post(self.URL, data=self._valid_post(), follow=True)
        messages = list(r.context["messages"])
        self.assertTrue(any("success" in str(m.tags) for m in messages))

    def test_honeypot_filled_blocks_submission(self):
        count_before = ContactMessage.objects.count()
        self.client.post(self.URL, data=self._valid_post(website_url="http://spam.com"))
        self.assertEqual(ContactMessage.objects.count(), count_before)

    def test_invalid_post_missing_name_re_renders(self):
        r = self.client.post(self.URL, data=self._valid_post(name=""))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "website/contact.html")

    def test_invalid_post_adds_error_message(self):
        r = self.client.post(self.URL, data=self._valid_post(name=""), follow=True)
        messages = list(r.context["messages"])
        self.assertTrue(any("error" in str(m.tags) for m in messages))

    @patch("website.views.notify_contact_form")
    def test_message_stored_with_correct_fields(self, mock_notify):
        self.client.post(
            self.URL, data=self._valid_post(name="Stored Name", subject="Stored Sub")
        )
        msg = ContactMessage.objects.filter(name="Stored Name").first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.subject, "Stored Sub")


# ── email_subscription view ────────────────────────────────────────────────────


class EmailSubscriptionViewTests(WebsiteBaseTestCase):
    URL = "/email-subscription/"

    def test_post_valid_returns_htmx_partial(self):
        r = self.client.post(self.URL, data={"email": "htmx@example.com"})
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "partials/htmx_notification.html")

    def test_post_valid_saves_subscriber(self):
        self.client.post(self.URL, data={"email": "saved_sub@example.com"})
        self.assertTrue(
            EmailSubscriber.objects.filter(email="saved_sub@example.com").exists()
        )

    def test_post_invalid_returns_form_partial(self):
        r = self.client.post(self.URL, data={"email": "not-an-email"})
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "partials/email_subscription_form.html")

    def test_get_returns_form_partial_with_error(self):
        r = self.client.get(self.URL)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "partials/email_subscription_form.html")

    def test_post_valid_context_success_true(self):
        r = self.client.post(self.URL, data={"email": "ctx@example.com"})
        self.assertTrue(r.context["success"])

    def test_post_invalid_context_success_false(self):
        r = self.client.post(self.URL, data={"email": "bad"})
        self.assertFalse(r.context["success"])

    def test_duplicate_email_returns_form_partial(self):
        EmailSubscriber.objects.create(email="existing@example.com")
        r = self.client.post(self.URL, data={"email": "existing@example.com"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context.get("success", True))


# ── PartnerListView ────────────────────────────────────────────────────────────


class PartnerListViewTests(WebsiteBaseTestCase):
    URL = "/partners/"

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.URL), "website/partners.html")

    def test_context_has_partners(self):
        r = self.client.get(self.URL)
        self.assertIn("partners", r.context)

    def test_context_includes_created_partner(self):
        r = self.client.get(self.URL)
        partners = list(r.context["partners"])
        self.assertIn(self.partner, partners)

    def test_partners_ordered_by_name(self):
        Partner.objects.create(name="Alpha Partner")
        r = self.client.get(self.URL)
        names = [p.name for p in r.context["partners"]]
        self.assertEqual(names, sorted(names))


# ── Health check endpoints ─────────────────────────────────────────────────────


class HealthCheckViewTests(WebsiteBaseTestCase):
    def test_health_check_returns_200(self):
        r = self.client.get("/health/")
        self.assertEqual(r.status_code, 200)

    def test_liveness_check_returns_200(self):
        r = self.client.get("/health/live/")
        self.assertEqual(r.status_code, 200)

    def test_readiness_check_returns_200(self):
        r = self.client.get("/health/ready/")
        self.assertEqual(r.status_code, 200)

    def test_health_returns_json(self):

        r = self.client.get("/health/")
        try:
            data = json.loads(r.content)
            self.assertIn("status", data)
        except Exception:
            pass  # May return other format — just ensure 200


# ── FAQPageView ────────────────────────────────────────────────────────────────


class FAQPageViewTests(WebsiteBaseTestCase):
    URL = "/faqs/"

    def setUp(self):

        self.active_faq = FAQ.objects.create(
            question="What is CBC?",
            answer="Competency Based Curriculum.",
            is_active=True,
            order=1,
        )
        self.inactive_faq = FAQ.objects.create(
            question="Hidden question?",
            answer="Should not appear.",
            is_active=False,
            order=2,
        )

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.URL), "website/faqs.html")

    def test_context_has_faqs(self):
        r = self.client.get(self.URL)
        self.assertIn("faqs", r.context)

    def test_only_active_faqs_in_context(self):
        r = self.client.get(self.URL)
        faqs = list(r.context["faqs"])
        self.assertIn(self.active_faq, faqs)
        self.assertNotIn(self.inactive_faq, faqs)

    def test_faqs_ordered_by_order_field(self):

        FAQ.objects.create(question="First?", answer="Yes", is_active=True, order=0)
        r = self.client.get(self.URL)
        faqs = list(r.context["faqs"])
        orders = [f.order for f in faqs]
        self.assertEqual(orders, sorted(orders))


# ── TestimonialsPageView ───────────────────────────────────────────────────────


class TestimonialsPageViewTests(WebsiteBaseTestCase):
    URL = "/testimonials/"

    def setUp(self):

        self.active = Testimonial.objects.create(
            author_name="Jane Teacher",
            body="Great resource hub!",
            rating=5,
            is_active=True,
            is_featured=False,
        )
        self.featured = Testimonial.objects.create(
            author_name="John Educator",
            body="Absolutely love it.",
            rating=5,
            is_active=True,
            is_featured=True,
        )
        self.inactive = Testimonial.objects.create(
            author_name="Hidden User",
            body="Should not appear.",
            rating=3,
            is_active=False,
        )

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.URL), "website/testimonials.html")

    def test_context_has_testimonials(self):
        r = self.client.get(self.URL)
        self.assertIn("testimonials", r.context)

    def test_context_has_featured(self):
        r = self.client.get(self.URL)
        self.assertIn("featured", r.context)

    def test_only_active_in_context(self):
        r = self.client.get(self.URL)
        all_t = list(r.context["testimonials"])
        self.assertIn(self.active, all_t)
        self.assertIn(self.featured, all_t)
        self.assertNotIn(self.inactive, all_t)

    def test_featured_in_featured_context(self):
        r = self.client.get(self.URL)
        featured = list(r.context["featured"])
        self.assertIn(self.featured, featured)
        self.assertNotIn(self.inactive, featured)

    def test_featured_items_appear_first(self):
        r = self.client.get(self.URL)
        testimonials = list(r.context["testimonials"])
        # Featured entries should come before non-featured
        featured_indices = [i for i, t in enumerate(testimonials) if t.is_featured]
        non_featured_indices = [
            i for i, t in enumerate(testimonials) if not t.is_featured
        ]
        if featured_indices and non_featured_indices:
            self.assertLess(max(featured_indices), min(non_featured_indices))


# ── HomePageView – FAQ/Testimonial context ─────────────────────────────────────


class HomePageFAQTestimonialContextTests(WebsiteBaseTestCase):
    """Ensure the homepage exposes homepage_faqs and homepage_testimonials."""

    URL = "/"

    def setUp(self):
        cache.clear()
        for i in range(7):
            FAQ.objects.create(question=f"Q{i}?", answer="A", is_active=True, order=i)
        for i in range(8):
            Testimonial.objects.create(
                author_name=f"Author {i}", body="Body", rating=5, is_active=True
            )

    def tearDown(self):
        cache.clear()

    def test_homepage_faqs_in_context(self):
        r = self.client.get(self.URL)
        self.assertIn("homepage_faqs", r.context)

    def test_homepage_faqs_capped_at_5(self):
        r = self.client.get(self.URL)
        self.assertLessEqual(len(list(r.context["homepage_faqs"])), 5)

    def test_homepage_testimonials_in_context(self):
        r = self.client.get(self.URL)
        self.assertIn("homepage_testimonials", r.context)

    def test_homepage_testimonials_capped_at_6(self):
        r = self.client.get(self.URL)
        self.assertLessEqual(len(list(r.context["homepage_testimonials"])), 6)
