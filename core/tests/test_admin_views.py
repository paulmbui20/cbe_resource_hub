"""
core/tests/test_admin_views.py

Tests for all views in core/admin_views.py:
  - Access control: anon / regular user / vendor blocked; admin allowed
  - Year CRUD: list, create, update, delete
  - Term CRUD: list, create, update, delete
  - AcademicSession CRUD: list, create, update, delete
"""

from django.urls import reverse

from core.models import AcademicSession, Term, Year
from core.tests.base import CoreBaseTestCase


# ── Access Control ─────────────────────────────────────────────────────────────

class CoreAccessControlTests(CoreBaseTestCase):

    def _get(self, name, kwargs=None):
        return self.client.get(reverse(name, kwargs=kwargs))

    def test_anonymous_denied_year_list(self):
        r = self._get("management:year_list")
        self.assertIn(r.status_code, [302, 403])

    def test_regular_user_denied_year_list(self):
        self.login_as_user()
        r = self._get("management:year_list")
        self.assertIn(r.status_code, [302, 403])

    def test_vendor_denied_year_list(self):
        self.login_as_vendor()
        r = self._get("management:year_list")
        self.assertIn(r.status_code, [302, 403])

    def test_admin_allowed_year_list(self):
        self.login_as_admin()
        r = self._get("management:year_list")
        self.assertEqual(r.status_code, 200)

    def test_anonymous_denied_term_list(self):
        r = self._get("management:term_list")
        self.assertIn(r.status_code, [302, 403])

    def test_admin_allowed_term_list(self):
        self.login_as_admin()
        r = self._get("management:term_list")
        self.assertEqual(r.status_code, 200)

    def test_anonymous_denied_academic_session_list(self):
        r = self._get("management:academic_session_list")
        self.assertIn(r.status_code, [302, 403])

    def test_admin_allowed_academic_session_list(self):
        self.login_as_admin()
        r = self._get("management:academic_session_list")
        self.assertEqual(r.status_code, 200)


# ── Year CRUD ──────────────────────────────────────────────────────────────────

class AdminYearListViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:year_list")

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.url), "admin/core/year_list.html")

    def test_context_has_years(self):
        self.assertIn("years", self.client.get(self.url).context)

    def test_created_year_appears_in_list(self):
        years = list(self.client.get(self.url).context["years"])
        self.assertIn(self.year, years)


class AdminYearCreateViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:year_create")

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_uses_generic_form_template(self):
        self.assertTemplateUsed(self.client.get(self.url), "admin/generic_form.html")

    def test_context_has_title(self):
        self.assertIn("title", self.client.get(self.url).context)

    def test_valid_post_creates_year(self):
        self.client.post(self.url, data={"year": 2077})
        self.assertTrue(Year.objects.filter(year=2077).exists())

    def test_valid_post_redirects_to_year_list(self):
        r = self.client.post(self.url, data={"year": 2078})
        self.assertRedirects(r, reverse("management:year_list"))

    def test_duplicate_year_re_renders_form(self):
        r = self.client.post(self.url, data={"year": self.year.year})
        self.assertEqual(r.status_code, 200)

    def test_blank_year_re_renders_form(self):
        r = self.client.post(self.url, data={"year": ""})
        self.assertEqual(r.status_code, 200)


class AdminYearUpdateViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = Year.objects.create(year=2060)
        self.url = reverse("management:year_update", kwargs={"pk": self.target.pk})

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_updates_year(self):
        self.client.post(self.url, data={"year": 2061})
        self.target.refresh_from_db()
        self.assertEqual(self.target.year, 2061)

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={"year": 2062})
        self.assertRedirects(r, reverse("management:year_list"))

    def test_nonexistent_year_returns_404(self):
        url = reverse("management:year_update", kwargs={"pk": 99999})
        self.assertEqual(self.client.get(url).status_code, 404)


class AdminYearDeleteViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = Year.objects.create(year=2070)
        self.url = reverse("management:year_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_year(self):
        self.client.post(self.url)
        self.assertFalse(Year.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:year_list"))

    def test_delete_nonexistent_returns_404(self):
        r = self.client.post(reverse("management:year_delete", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── Term CRUD ──────────────────────────────────────────────────────────────────

class AdminTermListViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        r = self.client.get(reverse("management:term_list"))
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:term_list")),
            "admin/core/term_list.html",
        )

    def test_context_has_terms(self):
        r = self.client.get(reverse("management:term_list"))
        self.assertIn("terms", r.context)


class AdminTermCreateViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:term_create")

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_creates_term(self):
        self.client.post(self.url, data={"term_number": 5})
        self.assertTrue(Term.objects.filter(term_number=5).exists())

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={"term_number": 6})
        self.assertRedirects(r, reverse("management:term_list"))

    def test_duplicate_term_number_re_renders(self):
        r = self.client.post(self.url, data={"term_number": self.term.term_number})
        self.assertEqual(r.status_code, 200)

    def test_blank_term_number_re_renders(self):
        r = self.client.post(self.url, data={"term_number": ""})
        self.assertEqual(r.status_code, 200)


class AdminTermUpdateViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = Term.objects.create(term_number=10)
        self.url = reverse("management:term_update", kwargs={"pk": self.target.pk})

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_updates_term(self):
        self.client.post(self.url, data={"term_number": 11})
        self.target.refresh_from_db()
        self.assertEqual(self.target.term_number, 11)

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={"term_number": 12})
        self.assertRedirects(r, reverse("management:term_list"))

    def test_nonexistent_term_returns_404(self):
        url = reverse("management:term_update", kwargs={"pk": 99999})
        self.assertEqual(self.client.get(url).status_code, 404)


class AdminTermDeleteViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = Term.objects.create(term_number=20)
        self.url = reverse("management:term_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_term(self):
        self.client.post(self.url)
        self.assertFalse(Term.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:term_list"))

    def test_delete_nonexistent_returns_404(self):
        r = self.client.post(reverse("management:term_delete", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── AcademicSession CRUD ───────────────────────────────────────────────────────

class AdminAcademicSessionListViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        r = self.client.get(reverse("management:academic_session_list"))
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:academic_session_list")),
            "admin/core/academic_session_list.html",
        )

    def test_context_has_academic_sessions(self):
        r = self.client.get(reverse("management:academic_session_list"))
        self.assertIn("academic_sessions", r.context)

    def test_session_appears_in_list(self):
        sessions = list(
            self.client.get(reverse("management:academic_session_list"))
            .context["academic_sessions"]
        )
        self.assertIn(self.session, sessions)


class AdminAcademicSessionCreateViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:academic_session_create")
        self.new_year = Year.objects.create(year=2080)
        self.new_term = Term.objects.create(term_number=3)

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_has_title(self):
        self.assertIn("title", self.client.get(self.url).context)

    def test_valid_post_creates_session(self):
        self.client.post(self.url, data={
            "current_year": self.new_year.pk,
            "current_term": self.new_term.pk,
        })
        self.assertTrue(
            AcademicSession.objects.filter(
                current_year=self.new_year, current_term=self.new_term
            ).exists()
        )

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={
            "current_year": self.new_year.pk,
            "current_term": self.new_term.pk,
        })
        self.assertRedirects(r, reverse("management:academic_session_list"))

    def test_duplicate_session_re_renders(self):
        r = self.client.post(self.url, data={
            "current_year": self.year.pk,
            "current_term": self.term.pk,
        })
        self.assertEqual(r.status_code, 200)

    def test_missing_year_re_renders(self):
        r = self.client.post(self.url, data={"current_term": self.new_term.pk})
        self.assertEqual(r.status_code, 200)


class AdminAcademicSessionUpdateViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.extra_year = Year.objects.create(year=2085)
        self.extra_term = Term.objects.create(term_number=13)
        self.target = AcademicSession.objects.create(
            current_year=self.extra_year,
            current_term=self.extra_term,
        )
        self.url = reverse(
            "management:academic_session_update", kwargs={"pk": self.target.pk}
        )

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_updates_session(self):
        alt_term = Term.objects.create(term_number=14)
        self.client.post(self.url, data={
            "current_year": self.extra_year.pk,
            "current_term": alt_term.pk,
        })
        self.target.refresh_from_db()
        self.assertEqual(self.target.current_term, alt_term)

    def test_valid_post_redirects(self):
        alt_term = Term.objects.create(term_number=15)
        r = self.client.post(self.url, data={
            "current_year": self.extra_year.pk,
            "current_term": alt_term.pk,
        })
        self.assertRedirects(r, reverse("management:academic_session_list"))

    def test_nonexistent_session_returns_404(self):
        url = reverse("management:academic_session_update", kwargs={"pk": 99999})
        self.assertEqual(self.client.get(url).status_code, 404)


class AdminAcademicSessionDeleteViewTests(CoreBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        y = Year.objects.create(year=2090)
        t = Term.objects.create(term_number=16)
        self.target = AcademicSession.objects.create(current_year=y, current_term=t)
        self.url = reverse(
            "management:academic_session_delete", kwargs={"pk": self.target.pk}
        )

    def test_post_deletes_session(self):
        self.client.post(self.url)
        self.assertFalse(AcademicSession.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:academic_session_list"))

    def test_delete_nonexistent_returns_404(self):
        r = self.client.post(
            reverse("management:academic_session_delete", kwargs={"pk": 99999})
        )
        self.assertEqual(r.status_code, 404)
