"""
website/tests/test_admin_views.py

Tests for all website admin views:
  - IsAdminMixin access control on every view
  - AdminDashboardView: GET 200, context keys
  - AdminContactMessageListView: GET 200, template, context, unread_count
  - AdminContactMessageDetailView: GET 200, auto-marks as read, 404
  - AdminContactMessageDeleteView: POST deletes, redirects, 404
  - AdminPartnerListView: GET 200, template
  - AdminPartnerCreateView: GET 200, POST creates partner, redirects
  - AdminPartnerUpdateView: GET 200, POST updates, 404
  - AdminPartnerDeleteView: POST deletes, redirects
  - AdminEmailSubscribersListView: GET 200, search filter, opted_out_count
  - AdminEmailSubscribersCreateView: GET 200, POST creates subscriber
  - AdminEmailSubscriberEdit: GET 200, POST updates
  - AdminEmailSubscriberDeleteView: POST deletes
"""

from django.test import TestCase
from django.urls import reverse

from website.models import ContactMessage, Partner, EmailSubscriber
from website.tests.base import WebsiteBaseTestCase


# ── Access Control ─────────────────────────────────────────────────────────────

class AdminWebsiteAccessControlTests(WebsiteBaseTestCase):

    def test_anonymous_denied_dashboard(self):
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn(r.status_code, [302, 403])

    def test_regular_user_denied_dashboard(self):
        self.login_as_user()
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn(r.status_code, [302, 403])

    def test_admin_allowed_dashboard(self):
        self.login_as_admin()
        r = self.client.get(reverse("management:dashboard"))
        self.assertEqual(r.status_code, 200)


# ── AdminDashboardView ─────────────────────────────────────────────────────────

class AdminDashboardViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        self.assertEqual(self.client.get(reverse("management:dashboard")).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:dashboard")),
            "admin/dashboard.html",
        )

    def test_context_has_total_users(self):
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn("total_users", r.context)

    def test_context_has_total_vendors(self):
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn("total_vendors", r.context)

    def test_context_has_total_resources(self):
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn("total_resources", r.context)

    def test_context_has_total_pages(self):
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn("total_pages", r.context)

    def test_context_has_unread_messages(self):
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn("unread_messages", r.context)

    def test_context_has_recent_users(self):
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn("recent_users", r.context)

    def test_context_has_recent_resources(self):
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn("recent_resources", r.context)

    def test_context_has_total_email_subscribers(self):
        r = self.client.get(reverse("management:dashboard"))
        self.assertIn("total_email_subscribers", r.context)

    def test_unread_messages_count_correct(self):
        unread = ContactMessage.objects.filter(is_read=False).count()
        r = self.client.get(reverse("management:dashboard"))
        self.assertEqual(r.context["unread_messages"], unread)


# ── AdminContactMessageListView ────────────────────────────────────────────────

class AdminContactMessageListViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        r = self.client.get(reverse("management:contact_list"))
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:contact_list")),
            "admin/contact_message_list.html",
        )

    def test_context_has_contact_messages(self):
        r = self.client.get(reverse("management:contact_list"))
        self.assertIn("contact_messages", r.context)

    def test_context_has_unread_count(self):
        r = self.client.get(reverse("management:contact_list"))
        self.assertIn("unread_count", r.context)

    def test_unread_count_correct(self):
        expected = ContactMessage.objects.filter(is_read=False).count()
        r = self.client.get(reverse("management:contact_list"))
        self.assertEqual(r.context["unread_count"], expected)


# ── AdminContactMessageDetailView ──────────────────────────────────────────────

class AdminContactMessageDetailViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:contact_detail", kwargs={"pk": self.contact_msg.pk})

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(self.url),
            "admin/contact_message_detail.html",
        )

    def test_context_has_msg(self):
        r = self.client.get(self.url)
        self.assertIn("msg", r.context)

    def test_auto_marks_as_read_on_get(self):
        msg = ContactMessage.objects.create(
            name="Unread Msg", subject="Sub", message="Body", is_read=False
        )
        self.client.get(reverse("management:contact_detail", kwargs={"pk": msg.pk}))
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_nonexistent_returns_404(self):
        r = self.client.get(reverse("management:contact_detail", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── AdminContactMessageDeleteView ──────────────────────────────────────────────

class AdminContactMessageDeleteViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.target = ContactMessage.objects.create(
            name="Delete Me", subject="Sub", message="Body"
        )
        self.url = reverse("management:contact_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_message(self):
        self.client.post(self.url)
        self.assertFalse(ContactMessage.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects_to_contact_list(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:contact_list"))

    def test_nonexistent_returns_404(self):
        r = self.client.post(reverse("management:contact_delete", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)

    def test_anonymous_denied(self):
        self.client.logout()
        r = self.client.post(self.url)
        self.assertIn(r.status_code, [302, 403])
        self.assertTrue(ContactMessage.objects.filter(pk=self.target.pk).exists())


# ── AdminPartnerListView ───────────────────────────────────────────────────────

class AdminPartnerListViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        r = self.client.get(reverse("management:partner_list"))
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:partner_list")),
            "admin/partner_list.html",
        )

    def test_context_has_partners(self):
        r = self.client.get(reverse("management:partner_list"))
        self.assertIn("partners", r.context)


# ── AdminPartnerCreateView ─────────────────────────────────────────────────────

class AdminPartnerCreateViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:partner_add")

    def _payload(self, **kw):
        defaults = {"name": "New Admin Partner", "banner_cta": "Join Now"}
        defaults.update(kw)
        return defaults

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_uses_seo_form_template(self):
        self.assertTemplateUsed(self.client.get(self.url), "admin/seo_form.html")

    def test_context_has_title(self):
        self.assertIn("title", self.client.get(self.url).context)

    def test_valid_post_creates_partner(self):
        self.client.post(self.url, data=self._payload())
        self.assertTrue(Partner.objects.filter(name="New Admin Partner").exists())

    def test_valid_post_redirects_to_list(self):
        r = self.client.post(self.url, data=self._payload(name="Redirect Partner"))
        self.assertRedirects(r, reverse("management:partner_list"))

    def test_invalid_post_missing_name_re_renders(self):
        r = self.client.post(self.url, data=self._payload(name=""))
        self.assertEqual(r.status_code, 200)


# ── AdminPartnerUpdateView ─────────────────────────────────────────────────────

class AdminPartnerUpdateViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:partner_edit", kwargs={"pk": self.partner.pk})

    def _payload(self, **kw):
        defaults = {
            "name": "Updated Partner Name",
            "banner_cta": "Learn More",
            "show_as_banner": False,
        }
        defaults.update(kw)
        return defaults

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_title_contains_partner_name(self):
        r = self.client.get(self.url)
        self.assertIn(self.partner.name, r.context["title"])

    def test_valid_post_updates_partner(self):
        self.client.post(self.url, data=self._payload())
        self.partner.refresh_from_db()
        self.assertEqual(self.partner.name, "Updated Partner Name")

    def test_valid_post_redirects_to_list(self):
        r = self.client.post(self.url, data=self._payload())
        self.assertRedirects(r, reverse("management:partner_list"))

    def test_nonexistent_returns_404(self):
        r = self.client.get(reverse("management:partner_edit", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── AdminPartnerDeleteView ─────────────────────────────────────────────────────

class AdminPartnerDeleteViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.target = Partner.objects.create(name="Delete Target Partner")
        self.url = reverse("management:partner_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_partner(self):
        self.client.post(self.url)
        self.assertFalse(Partner.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects_to_partner_list(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:partner_list"))

    def test_nonexistent_returns_404(self):
        r = self.client.post(reverse("management:partner_delete", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── AdminEmailSubscribersListView ──────────────────────────────────────────────

class AdminEmailSubscribersListViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        r = self.client.get(reverse("management:email_subscribers"))
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:email_subscribers")),
            "admin/email_subscribers_list.html",
        )

    def test_context_has_email_subscribers(self):
        r = self.client.get(reverse("management:email_subscribers"))
        self.assertIn("email_subscribers", r.context)

    def test_context_has_opted_out_count(self):
        r = self.client.get(reverse("management:email_subscribers"))
        self.assertIn("opted_out_count", r.context)

    def test_search_filter_by_email(self):
        r = self.client.get(reverse("management:email_subscribers") + "?q=subscriber")
        subs = list(r.context["email_subscribers"])
        self.assertTrue(all("subscriber" in s.email.lower() for s in subs))

    def test_search_no_match_returns_empty(self):
        r = self.client.get(reverse("management:email_subscribers") + "?q=ZZZNOMATCH")
        self.assertEqual(list(r.context["email_subscribers"]), [])


# ── AdminEmailSubscribersCreateView ───────────────────────────────────────────

class AdminEmailSubscriberCreateViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:email_subscriber_add")

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_creates_subscriber(self):
        self.client.post(self.url, data={
            "email": "admin_created@example.com",
            "full_name": "Admin Created",
            "opted_out": False,
        })
        self.assertTrue(EmailSubscriber.objects.filter(email="admin_created@example.com").exists())

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={
            "email": "redirect_sub@example.com",
            "full_name": "Redirect Sub",
            "opted_out": False,
        })
        self.assertRedirects(r, reverse("management:email_subscribers"))


# ── AdminEmailSubscriberEdit ───────────────────────────────────────────────────

class AdminEmailSubscriberEditViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:email_subscriber_edit", kwargs={"pk": self.subscriber.pk})

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_updates_subscriber(self):
        self.client.post(self.url, data={
            "email": self.subscriber.email,
            "full_name": "Updated Name",
            "opted_out": False,
        })
        self.subscriber.refresh_from_db()
        self.assertEqual(self.subscriber.full_name, "Updated Name")

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={
            "email": self.subscriber.email,
            "full_name": "Redirect Test",
            "opted_out": False,
        })
        self.assertRedirects(r, reverse("management:email_subscribers"))

    def test_nonexistent_returns_404(self):
        r = self.client.get(reverse("management:email_subscriber_edit", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── AdminEmailSubscriberDeleteView ─────────────────────────────────────────────

class AdminEmailSubscriberDeleteViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.target = EmailSubscriber.objects.create(email="delete_me_sub@example.com")
        self.url = reverse("management:email_subscribers_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_subscriber(self):
        self.client.post(self.url)
        self.assertFalse(EmailSubscriber.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects_to_list(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:email_subscribers"))

    def test_nonexistent_returns_404(self):
        r = self.client.post(
            reverse("management:email_subscribers_delete", kwargs={"pk": 99999})
        )
        self.assertEqual(r.status_code, 404)


# ── AdminTestimonialListView ───────────────────────────────────────────────────

class AdminTestimonialListViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        from website.models import Testimonial
        self.testimonial = Testimonial.objects.create(
            author_name="Jane Doe", body="Great platform!", rating=5
        )

    def test_returns_200(self):
        r = self.client.get(reverse("management:testimonial_list"))
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:testimonial_list")),
            "admin/testimonial_list.html",
        )

    def test_context_has_testimonials(self):
        r = self.client.get(reverse("management:testimonial_list"))
        self.assertIn("testimonials", r.context)


class AdminTestimonialCreateViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:testimonial_add")

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_creates_testimonial(self):
        from website.models import Testimonial
        self.client.post(self.url, data={
            "author_name": "Test Author", "body": "Amazing!", "rating": 5,
            "is_featured": False, "is_active": True, "order": 0,
        })
        self.assertTrue(Testimonial.objects.filter(author_name="Test Author").exists())

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={
            "author_name": "Redirect Author", "body": "Great!", "rating": 4,
            "is_featured": False, "is_active": True, "order": 0,
        })
        self.assertRedirects(r, reverse("management:testimonial_list"))


class AdminTestimonialUpdateViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        from website.models import Testimonial
        self.obj = Testimonial.objects.create(author_name="Old Name", body="Old body", rating=3)
        self.url = reverse("management:testimonial_edit", kwargs={"pk": self.obj.pk})

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_updates(self):
        self.client.post(self.url, data={
            "author_name": "New Name", "body": "New body", "rating": 5,
            "is_featured": False, "is_active": True, "order": 0,
        })
        self.obj.refresh_from_db()
        self.assertEqual(self.obj.author_name, "New Name")

    def test_nonexistent_returns_404(self):
        r = self.client.get(reverse("management:testimonial_edit", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


class AdminTestimonialDeleteViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        from website.models import Testimonial
        self.obj = Testimonial.objects.create(author_name="Delete Me", body="body", rating=5)
        self.url = reverse("management:testimonial_delete", kwargs={"pk": self.obj.pk})

    def test_post_deletes(self):
        from website.models import Testimonial
        self.client.post(self.url)
        self.assertFalse(Testimonial.objects.filter(pk=self.obj.pk).exists())

    def test_post_redirects(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:testimonial_list"))


# ── AdminFAQListView ───────────────────────────────────────────────────────────

class AdminFAQListViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        from website.models import FAQ
        self.faq = FAQ.objects.create(question="What is CBC?", answer="Competency Based Curriculum.")

    def test_returns_200(self):
        r = self.client.get(reverse("management:faq_list"))
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:faq_list")),
            "admin/faq_list.html",
        )

    def test_context_has_faqs(self):
        r = self.client.get(reverse("management:faq_list"))
        self.assertIn("faqs", r.context)


class AdminFAQCreateViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:faq_add")

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_creates_faq(self):
        from website.models import FAQ
        self.client.post(self.url, data={
            "question": "New FAQ question?", "answer": "Answer here.",
            "is_active": True, "order": 1,
        })
        self.assertTrue(FAQ.objects.filter(question="New FAQ question?").exists())

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={
            "question": "Another FAQ?", "answer": "Yes.",
            "is_active": True, "order": 2,
        })
        self.assertRedirects(r, reverse("management:faq_list"))


class AdminFAQUpdateViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        from website.models import FAQ
        self.obj = FAQ.objects.create(question="Old Q?", answer="Old A.")
        self.url = reverse("management:faq_edit", kwargs={"pk": self.obj.pk})

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_updates(self):
        self.client.post(self.url, data={
            "question": "Updated Q?", "answer": "Updated A.",
            "is_active": True, "order": 0,
        })
        self.obj.refresh_from_db()
        self.assertEqual(self.obj.question, "Updated Q?")

    def test_nonexistent_returns_404(self):
        r = self.client.get(reverse("management:faq_edit", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


class AdminFAQDeleteViewTests(WebsiteBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        from website.models import FAQ
        self.obj = FAQ.objects.create(question="Delete Me?", answer="Yes.")
        self.url = reverse("management:faq_delete", kwargs={"pk": self.obj.pk})

    def test_post_deletes(self):
        from website.models import FAQ
        self.client.post(self.url)
        self.assertFalse(FAQ.objects.filter(pk=self.obj.pk).exists())

    def test_post_redirects(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:faq_list"))
