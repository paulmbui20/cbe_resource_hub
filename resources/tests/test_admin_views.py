"""
resources/tests/test_admin_views.py

Tests for admin_views.py (AdminResource CRUD) and
admin_dependency_views.py (EducationLevel / Grade / LearningArea CRUD).

Covers:
  - IsAdminMixin: anonymous / regular user / vendor blocked; admin allowed
  - AdminResourceListView: list, search filter
  - AdminResourceCreateView: GET, POST valid/invalid
  - AdminResourceUpdateView: GET, POST valid, 404
  - AdminResourceDeleteView: POST deletes, 404
  - AdminEducationLevel / AdminGrade / AdminLearningArea CRUD (same pattern)
"""

from django.urls import reverse

from resources.models import EducationLevel, Grade, LearningArea, ResourceItem
from resources.tests.base import ResourceBaseTestCase, make_pdf


# ── Access Control ─────────────────────────────────────────────────────────────

class AdminResourceAccessControlTests(ResourceBaseTestCase):

    def _get(self, name, kwargs=None):
        return self.client.get(reverse(name, kwargs=kwargs))

    def test_anonymous_denied_resource_list(self):
        self.assertIn(self._get("management:resource_list").status_code, [302, 403])

    def test_regular_user_denied_resource_list(self):
        self.login_as_user()
        self.assertIn(self._get("management:resource_list").status_code, [302, 403])

    def test_vendor_denied_resource_list(self):
        self.login_as_vendor()
        self.assertIn(self._get("management:resource_list").status_code, [302, 403])

    def test_admin_allowed_resource_list(self):
        self.login_as_admin()
        self.assertEqual(self._get("management:resource_list").status_code, 200)


# ── AdminResourceListView ──────────────────────────────────────────────────────

class AdminResourceListViewTests(ResourceBaseTestCase):

    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        self.assertEqual(self.client.get(reverse("management:resource_list")).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:resource_list")),
            "admin/resource_list.html",
        )

    def test_context_has_resources(self):
        r = self.client.get(reverse("management:resource_list"))
        self.assertIn("resources", r.context)

    def test_search_filter_by_title(self):
        r = self.client.get(reverse("management:resource_list") + "?q=Sample")
        resources = list(r.context["resources"])
        self.assertTrue(all("sample" in res.title.lower() for res in resources))

    def test_search_no_match_empty(self):
        r = self.client.get(reverse("management:resource_list") + "?q=ZZZNOMATCH")
        self.assertEqual(list(r.context["resources"]), [])


# ── AdminResourceCreateView ────────────────────────────────────────────────────

class AdminResourceCreateViewTests(ResourceBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:resource_add")

    def _payload(self, **kw):
        defaults = {
            "title": "Admin Created Resource",
            "resource_type": "notes",
            "description": "<p>content</p>",
            "grade": self.grade.pk,
            "learning_area": self.learning_area.pk,
            "academic_session": self.session.pk,
            "is_free": True,
        }
        defaults.update(kw)
        return defaults

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_uses_seo_form_template(self):
        self.assertTemplateUsed(self.client.get(self.url), "admin/seo_form.html")

    def test_context_has_title(self):
        self.assertIn("title", self.client.get(self.url).context)

    def test_valid_post_creates_resource(self):
        f = make_pdf("admin_create.pdf")
        self.client.post(self.url, data={**self._payload(), "file": f})
        self.assertTrue(ResourceItem.objects.filter(title="Admin Created Resource").exists())

    def test_valid_post_redirects_to_resource_list(self):
        f = make_pdf("admin_redir.pdf")
        r = self.client.post(self.url, data={**self._payload(title="Redirect Resource"), "file": f})
        self.assertRedirects(r, reverse("management:resource_list"))

    def test_invalid_post_missing_title_re_renders(self):
        f = make_pdf("invalid.pdf")
        r = self.client.post(self.url, data={**self._payload(title=""), "file": f})
        self.assertEqual(r.status_code, 200)


# ── AdminResourceUpdateView ────────────────────────────────────────────────────

class AdminResourceUpdateViewTests(ResourceBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.target = self.make_resource(title="Update Target")
        self.url = reverse("management:resource_edit", kwargs={"pk": self.target.pk})

    def _payload(self, **kw):
        defaults = {
            "title": "Updated by Admin",
            "resource_type": "textbook",
            "description": "<p>updated</p>",
            "grade": self.grade.pk,
            "learning_area": self.learning_area.pk,
            "is_free": True,
        }
        defaults.update(kw)
        return defaults

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_title_contains_resource_title(self):
        r = self.client.get(self.url)
        self.assertIn(self.target.title, r.context["title"])

    def test_valid_post_updates_resource(self):
        f = make_pdf("upd.pdf")
        self.client.post(self.url, data={**self._payload(), "file": f})
        self.target.refresh_from_db()
        self.assertEqual(self.target.title, "Updated by Admin")

    def test_valid_post_redirects(self):
        f = make_pdf("upd2.pdf")
        r = self.client.post(self.url, data={**self._payload(), "file": f})
        self.assertRedirects(r, reverse("management:resource_list"))

    def test_nonexistent_resource_returns_404(self):
        url = reverse("management:resource_edit", kwargs={"pk": 99999})
        self.assertEqual(self.client.get(url).status_code, 404)


# ── AdminResourceDeleteView ────────────────────────────────────────────────────

class AdminResourceDeleteViewTests(ResourceBaseTestCase):

    def setUp(self):
        self.login_as_admin()
        self.target = self.make_resource(title="Admin Delete Target")
        self.url = reverse("management:resource_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_resource(self):
        self.client.post(self.url)
        self.assertFalse(ResourceItem.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects_to_resource_list(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:resource_list"))

    def test_nonexistent_returns_404(self):
        r = self.client.post(reverse("management:resource_delete", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── Education Level Admin CRUD ─────────────────────────────────────────────────

class AdminEducationLevelCRUDTests(ResourceBaseTestCase):

    def setUp(self):
        self.login_as_admin()

    def test_level_list_returns_200(self):
        r = self.client.get(reverse("management:level_list"))
        self.assertEqual(r.status_code, 200)

    def test_level_create_get_returns_200(self):
        r = self.client.get(reverse("management:level_add"))
        self.assertEqual(r.status_code, 200)

    def test_level_create_post_creates_level(self):
        self.client.post(reverse("management:level_add"),
                         data={"name": "Tertiary", "order": 10,
                               "meta_title": "Tertiary", "slug": "tertiary"})
        self.assertTrue(EducationLevel.objects.filter(name="Tertiary").exists())

    def test_level_create_redirects(self):
        r = self.client.post(reverse("management:level_add"),
                             data={"name": "Post-Secondary", "order": 11,
                                   "meta_title": "Post-Secondary", "slug": "post-secondary"})
        self.assertRedirects(r, reverse("management:level_list"))

    def test_level_update_post_updates(self):
        lvl = EducationLevel.objects.create(name="Old Level Name", order=20)
        r = self.client.post(
            reverse("management:level_edit", kwargs={"pk": lvl.pk}),
            data={"name": "New Level Name", "order": 20,
                  "meta_title": "New Level Name", "slug": lvl.slug},
        )
        lvl.refresh_from_db()
        self.assertEqual(lvl.name, "New Level Name")

    def test_level_delete_post_deletes(self):
        lvl = EducationLevel.objects.create(name="Delete Level", order=30)
        self.client.post(reverse("management:level_delete", kwargs={"pk": lvl.pk}))
        self.assertFalse(EducationLevel.objects.filter(pk=lvl.pk).exists())

    def test_level_update_nonexistent_returns_404(self):
        r = self.client.get(reverse("management:level_edit", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── Grade Admin CRUD ───────────────────────────────────────────────────────────

class AdminGradeCRUDTests(ResourceBaseTestCase):

    def setUp(self):
        self.login_as_admin()

    def test_grade_list_returns_200(self):
        r = self.client.get(reverse("management:grade_list"))
        self.assertEqual(r.status_code, 200)

    def test_grade_create_get_returns_200(self):
        r = self.client.get(reverse("management:grade_add"))
        self.assertEqual(r.status_code, 200)

    def test_grade_create_post_creates_grade(self):
        new_level = EducationLevel.objects.create(name="Admin Level", order=50)
        self.client.post(
            reverse("management:grade_add"),
            data={"level": new_level.pk, "name": "Grade Admin", "order": 1,
                  "meta_title": "Grade Admin", "slug": "grade-admin"},
        )
        self.assertTrue(Grade.objects.filter(name="Grade Admin").exists())

    def test_grade_create_redirects(self):
        new_level = EducationLevel.objects.create(name="Admin Level 2", order=51)
        r = self.client.post(
            reverse("management:grade_add"),
            data={"level": new_level.pk, "name": "Grade Redirect", "order": 2,
                  "meta_title": "Grade Redirect", "slug": "grade-redirect"},
        )
        self.assertRedirects(r, reverse("management:grade_list"))

    def test_grade_update_nonexistent_returns_404(self):
        r = self.client.get(reverse("management:grade_edit", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── Learning Area Admin CRUD ───────────────────────────────────────────────────

class AdminLearningAreaCRUDTests(ResourceBaseTestCase):

    def setUp(self):
        self.login_as_admin()

    def test_learningarea_list_returns_200(self):
        r = self.client.get(reverse("management:learningarea_list"))
        self.assertEqual(r.status_code, 200)

    def test_learningarea_create_get_returns_200(self):
        r = self.client.get(reverse("management:learningarea_add"))
        self.assertEqual(r.status_code, 200)

    def test_learningarea_create_post_creates(self):
        self.client.post(
            reverse("management:learningarea_add"),
            data={"name": "Creative Arts", "meta_title": "Creative Arts",
                  "slug": "creative-arts"},
        )
        self.assertTrue(LearningArea.objects.filter(name="Creative Arts").exists())

    def test_learningarea_create_redirects(self):
        r = self.client.post(
            reverse("management:learningarea_add"),
            data={"name": "Integrated Science", "meta_title": "Integrated Science",
                  "slug": "integrated-science"},
        )
        self.assertRedirects(r, reverse("management:learningarea_list"))

    def test_learningarea_delete_post_deletes(self):
        la = LearningArea.objects.create(name="Temp Area")
        self.client.post(reverse("management:learningarea_delete", kwargs={"pk": la.pk}))
        self.assertFalse(LearningArea.objects.filter(pk=la.pk).exists())

    def test_learningarea_update_nonexistent_returns_404(self):
        r = self.client.get(reverse("management:learningarea_edit", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)
