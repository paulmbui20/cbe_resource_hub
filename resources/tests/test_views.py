"""
resources/tests/test_views.py

URL name reference (from resources/urls.py, app_name='resources'):
  list                     → ResourceListView
  resource_detail          → ResourceDetailView (slug)
  resource_increment_downloads → increment_downloads (slug)
  toggle_favorite          → ToggleFavoriteView (slug)
  type_detail              → ResourceTypeDetailView (resource_type)
  education_level_details  → EducationLevelDetailsView (slug)
  learning_area_details    → LearningAreaDetailsView (slug)
  grade_details            → GradeDetailsView (slug)
  academic_session_detail  → AcademicSessionDetailView (slug)
  learning_areas_list      → LearningAreaListView
  grade_list               → GradeListView
  academic_session_list    → AcademicSessionListView
  manage_add               → ResourceCreateView
  manage_edit              → ResourceUpdateView (slug)
  manage_delete            → ResourceDeleteView (slug)
"""

from django.core.cache import cache
from django.urls import reverse

from resources.models import ResourceItem
from resources.tests.base import ResourceBaseTestCase, make_pdf


class ResourceListViewTests(ResourceBaseTestCase):

    URL = "/resources/"

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_200(self):
        r = self.client.get(self.URL)
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.URL), "resources/resource_list.html")

    def test_context_has_resources(self):
        self.assertIn("resources", self.client.get(self.URL).context)

    def test_context_has_education_levels(self):
        self.assertIn("education_levels", self.client.get(self.URL).context)

    def test_context_has_grades(self):
        self.assertIn("grades", self.client.get(self.URL).context)

    def test_context_has_learning_areas(self):
        self.assertIn("learning_areas", self.client.get(self.URL).context)

    def test_context_has_resource_types(self):
        self.assertIn("resource_types", self.client.get(self.URL).context)

    def test_htmx_returns_partial_template(self):
        r = self.client.get(self.URL, HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(r, "resources/partials/resource_cards.html")

    def test_suggestions_param_returns_suggestions_partial(self):
        r = self.client.get(self.URL + "?suggestions=1&q=sample")
        self.assertTemplateUsed(r, "resources/partials/search_suggestions.html")

    def test_filter_by_grade(self):
        r = self.client.get(self.URL + f"?grade={self.grade.pk}")
        resources = list(r.context["resources"])
        self.assertTrue(all(res.grade_id == self.grade.pk for res in resources))

    def test_filter_by_learning_area(self):
        r = self.client.get(self.URL + f"?area={self.learning_area.pk}")
        resources = list(r.context["resources"])
        self.assertTrue(all(res.learning_area_id == self.learning_area.pk for res in resources))

    def test_filter_by_level(self):
        r = self.client.get(self.URL + f"?level={self.level.pk}")
        resources = list(r.context["resources"])
        self.assertTrue(all(res.grade.level_id == self.level.pk for res in resources))

    def test_filter_by_resource_type(self):
        r = self.client.get(self.URL + "?resource_type=notes")
        resources = list(r.context["resources"])
        self.assertTrue(all(res.resource_type == "notes" for res in resources))

    def test_search_by_title(self):
        r = self.client.get(self.URL + "?q=Sample")
        resources = list(r.context["resources"])
        titles = [res.title for res in resources]
        self.assertIn("Sample Resource", titles)

    def test_search_no_match_returns_empty(self):
        r = self.client.get(self.URL + "?q=ZZZNOMATCH")
        self.assertEqual(list(r.context["resources"]), [])

    def test_unauthenticated_user_favorite_ids_empty(self):
        r = self.client.get(self.URL)
        self.assertEqual(r.context["user_favorite_ids"], set())

    def test_authenticated_user_favorite_ids_present(self):
        self.login_as_user()
        self.regular_user.favorites.add(self.resource)
        r = self.client.get(self.URL)
        self.assertIn(self.resource.pk, r.context["user_favorite_ids"])
        self.regular_user.favorites.clear()

    def test_only_free_resources_shown(self):
        paid = self.make_resource(title="Paid Resource", is_free=False)
        r = self.client.get(self.URL)
        pks = [res.pk for res in r.context["resources"]]
        self.assertNotIn(paid.pk, pks)


class ResourceDetailViewTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _url(self):
        return reverse("resources:resource_detail", kwargs={"slug": self.resource.slug})

    def test_returns_200(self):
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self._url()), "resources/resource_detail.html")

    def test_context_has_resource(self):
        r = self.client.get(self._url())
        self.assertIn("resource", r.context)
        self.assertEqual(r.context["resource"].pk, self.resource.pk)

    def test_missing_slug_returns_404(self):
        r = self.client.get(reverse("resources:resource_detail", kwargs={"slug": "no-such-slug"}))
        self.assertEqual(r.status_code, 404)

    def test_unauthenticated_favorite_ids_empty(self):
        r = self.client.get(self._url())
        self.assertEqual(r.context["user_favorite_ids"], set())


class IncrementDownloadsViewTests(ResourceBaseTestCase):

    def _url(self, slug=None):
        return reverse("resources:resource_increment_downloads",
                       kwargs={"slug": slug or self.resource.slug})

    def test_post_increments_download_count(self):
        initial = self.resource.downloads
        self.client.post(self._url())
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.downloads, initial + 1)

    def test_post_returns_json_success(self):
        import json
        r = self.client.post(self._url())
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertIn("success", data)

    def test_get_not_allowed(self):
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 405)

    def test_missing_slug_returns_404_json(self):
        import json
        r = self.client.post(self._url("no-such-slug"))
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", json.loads(r.content))


class ToggleFavoriteViewTests(ResourceBaseTestCase):

    def _url(self):
        return reverse("resources:toggle_favorite", kwargs={"slug": self.resource.slug})

    def test_requires_login(self):
        r = self.client.post(self._url())
        self.assertIn(r.status_code, [302, 403])

    def test_adds_to_favorites(self):
        self.login_as_user()
        self.client.post(self._url())
        self.assertIn(self.resource, self.regular_user.favorites.all())

    def test_removes_from_favorites_when_already_favorited(self):
        self.login_as_user()
        self.regular_user.favorites.add(self.resource)
        self.client.post(self._url())
        self.assertNotIn(self.resource, self.regular_user.favorites.all())

    def test_htmx_returns_html_snippet(self):
        self.login_as_user()
        r = self.client.post(self._url(), HTTP_HX_REQUEST="true")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"favorite", r.content.lower())

    def test_non_htmx_redirects_to_resource(self):
        self.login_as_user()
        r = self.client.post(self._url())
        self.assertRedirects(r, self.resource.get_absolute_url(),
                             fetch_redirect_response=False)


class ResourceTypeDetailViewTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _url(self, rtype="notes"):
        return reverse("resources:type_detail", kwargs={"resource_type": rtype})

    def test_returns_200(self):
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self._url()),
                                "resources/resource_type_detail.html")

    def test_context_has_type_label(self):
        r = self.client.get(self._url("notes"))
        self.assertIn("resource_type_label", r.context)

    def test_context_has_type_icon(self):
        r = self.client.get(self._url("notes"))
        self.assertIn("resource_type_icon", r.context)

    def test_unknown_type_still_returns_200(self):
        r = self.client.get(self._url("unknown_type"))
        self.assertEqual(r.status_code, 200)

    def test_htmx_returns_partial(self):
        r = self.client.get(self._url(), HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(r, "resources/partials/resource_cards.html")

    def test_search_filters_results(self):
        r = self.client.get(self._url() + "?q=Sample")
        resources = list(r.context["resources"])
        self.assertTrue(all("sample" in res.title.lower() for res in resources))

    def test_only_matching_type_shown(self):
        self.make_resource(title="Textbook Type", resource_type="textbook")
        r = self.client.get(self._url("notes"))
        resources = list(r.context["resources"])
        self.assertTrue(all(res.resource_type == "notes" for res in resources))


class EducationLevelDetailsViewTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _url(self, slug=None):
        return reverse("resources:education_level_details",
                       kwargs={"slug": slug or self.level.slug})

    def test_returns_200(self):
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self._url()),
                                "resources/education_level_details.html")

    def test_context_has_education_level(self):
        r = self.client.get(self._url())
        self.assertIn("education_level", r.context)

    def test_missing_slug_returns_404(self):
        r = self.client.get(self._url("no-such-level"))
        self.assertEqual(r.status_code, 404)

    def test_htmx_returns_partial(self):
        r = self.client.get(self._url(), HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(r, "resources/partials/resource_cards.html")

    def test_filter_by_learning_area(self):
        r = self.client.get(self._url() + f"?learning_area={self.learning_area.pk}")
        resources = list(r.context["resources"])
        self.assertTrue(all(res.learning_area_id == self.learning_area.pk for res in resources))


class LearningAreaDetailsViewTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _url(self):
        return reverse("resources:learning_area_details",
                       kwargs={"slug": self.learning_area.slug})

    def test_returns_200(self):
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self._url()),
                                "resources/learning_area_details.html")

    def test_context_has_learning_area(self):
        r = self.client.get(self._url())
        self.assertIn("learning_area", r.context)

    def test_htmx_returns_partial(self):
        r = self.client.get(self._url(), HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(r, "resources/partials/resource_cards.html")

    def test_filter_by_resource_type(self):
        r = self.client.get(self._url() + "?resource_type=notes")
        resources = list(r.context["resources"])
        self.assertTrue(all(res.resource_type == "notes" for res in resources))

    def test_missing_slug_returns_404(self):
        r = self.client.get(
            reverse("resources:learning_area_details", kwargs={"slug": "no-area"})
        )
        self.assertEqual(r.status_code, 404)


class GradeDetailsViewTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _url(self):
        return reverse("resources:grade_details", kwargs={"slug": self.grade.slug})

    def test_returns_200(self):
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self._url()),
                                "resources/grade_details.html")

    def test_context_has_grade(self):
        r = self.client.get(self._url())
        self.assertIn("grade", r.context)

    def test_htmx_returns_partial(self):
        r = self.client.get(self._url(), HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(r, "resources/partials/resource_cards.html")

    def test_missing_slug_returns_404(self):
        r = self.client.get(reverse("resources:grade_details", kwargs={"slug": "no-grade"}))
        self.assertEqual(r.status_code, 404)


class AcademicSessionDetailViewTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _url(self):
        return reverse("resources:academic_session_detail",
                       kwargs={"slug": self.session.slug})

    def test_returns_200(self):
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self._url()),
                                "resources/academic_session_detail.html")

    def test_context_has_academic_session(self):
        r = self.client.get(self._url())
        self.assertIn("academic_session", r.context)

    def test_htmx_returns_partial(self):
        r = self.client.get(self._url(), HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(r, "resources/partials/resource_cards.html")

    def test_missing_slug_returns_404(self):
        r = self.client.get(
            reverse("resources:academic_session_detail", kwargs={"slug": "no-session"})
        )
        self.assertEqual(r.status_code, 404)


class LearningAreaListViewTests(ResourceBaseTestCase):

    URL = "/resources/learning-areas/"

    def _list_url(self):
        return reverse("resources:learning_areas_list")

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.URL), "resources/learning_areas_list.html")

    def test_context_has_filters(self):
        self.assertIn("filters", self.client.get(self.URL).context)

    def test_search_filters_by_name(self):
        r = self.client.get(self.URL + "?q=Math")
        filters = list(r.context["filters"])
        self.assertTrue(all("math" in f.name.lower() for f in filters))

    def test_htmx_returns_partial(self):
        r = self.client.get(self.URL, HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(r, "resources/partials/filter_cards.html")


class GradeListViewTests(ResourceBaseTestCase):

    URL = "/resources/grades/"

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.URL), "resources/grade_list.html")

    def test_context_has_filters(self):
        self.assertIn("filters", self.client.get(self.URL).context)

    def test_search_filters_by_name(self):
        r = self.client.get(self.URL + "?q=Grade 1")
        filters = list(r.context["filters"])
        self.assertTrue(all("grade" in f.name.lower() for f in filters))

    def test_htmx_returns_partial(self):
        r = self.client.get(self.URL, HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(r, "resources/partials/filter_cards.html")


class AcademicSessionListViewTests(ResourceBaseTestCase):

    URL = "/resources/academic-sessions/"

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.URL),
                                "resources/academic_session_list.html")

    def test_context_has_academic_sessions(self):
        self.assertIn("academic_sessions", self.client.get(self.URL).context)

    def test_htmx_returns_partial(self):
        r = self.client.get(self.URL, HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(r, "resources/partials/academic_sessions_cards.html")


class ResourceCreateViewTests(ResourceBaseTestCase):

    URL = reverse_lazy = None  # use _url() instead

    def _url(self):
        return reverse("resources:manage_add")

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _payload(self, **kw):
        data = {
            "title": "Uploaded Resource",
            "resource_type": "notes",
            "description": "<p>desc</p>",
            "grade": self.grade.pk,
            "learning_area": self.learning_area.pk,
            "academic_session": self.session.pk,
            "is_free": True,
        }
        data.update(kw)
        return data

    def test_anonymous_denied(self):
        r = self.client.get(self._url())
        self.assertIn(r.status_code, [302, 403])

    def test_regular_user_denied(self):
        self.login_as_user()
        r = self.client.get(self._url())
        self.assertIn(r.status_code, [302, 403])

    def test_vendor_allowed(self):
        self.login_as_vendor()
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_admin_allowed(self):
        self.login_as_admin()
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_valid_post_creates_resource(self):
        self.login_as_vendor()
        f = make_pdf("create.pdf")
        self.client.post(self._url(), data={**self._payload(), "file": f})
        self.assertTrue(
            ResourceItem.objects.filter(title="Uploaded Resource").exists()
        )

    def test_valid_post_sets_vendor_to_current_user(self):
        self.login_as_vendor()
        f = make_pdf("vendor.pdf")
        self.client.post(self._url(), data={**self._payload(title="Vendor Upload"), "file": f})
        r = ResourceItem.objects.filter(title="Vendor Upload").first()
        if r:
            self.assertEqual(r.vendor, self.vendor)

    def test_valid_post_redirects_to_dashboard(self):
        self.login_as_vendor()
        f = make_pdf("redir.pdf")
        r = self.client.post(self._url(), data={**self._payload(title="Redirect Test"), "file": f})
        self.assertRedirects(r, reverse("accounts:dashboard"), fetch_redirect_response=False)


class ResourceUpdateViewTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()
        self.owned = ResourceItem.objects.create(
            title="Owned Resource",
            description="<p>d</p>",
            grade=self.grade,
            learning_area=self.learning_area,
            file=make_pdf("owned.pdf"),
            vendor=self.vendor,
            is_free=True,
            resource_type="notes",
        )

    def tearDown(self):
        cache.clear()

    def _url(self, slug=None):
        return reverse("resources:manage_edit",
                       kwargs={"slug": slug or self.owned.slug})

    def _payload(self, **kw):
        defaults = {
            "title": "Updated Title",
            "resource_type": "textbook",
            "description": "<p>Updated desc</p>",
            "grade": self.grade.pk,
            "learning_area": self.learning_area.pk,
            "is_free": True,
        }
        defaults.update(kw)
        return defaults

    def test_anonymous_denied(self):
        r = self.client.get(self._url())
        self.assertIn(r.status_code, [302, 403])

    def test_regular_user_denied(self):
        self.login_as_user()
        r = self.client.get(self._url())
        self.assertIn(r.status_code, [302, 403])

    def test_vendor_can_edit_own_resource(self):
        self.login_as_vendor()
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_vendor_cannot_edit_others_resource(self):
        other = self.make_resource(title="Others Resource", vendor=self.admin)
        self.login_as_vendor()
        r = self.client.get(self._url(other.slug))
        self.assertEqual(r.status_code, 404)

    def test_admin_can_edit_any_resource(self):
        self.login_as_admin()
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_valid_post_updates_resource(self):
        self.login_as_vendor()
        f = make_pdf("upd.pdf")
        self.client.post(self._url(), data={**self._payload(), "file": f})
        self.owned.refresh_from_db()
        self.assertEqual(self.owned.title, "Updated Title")


class ResourceDeleteViewTests(ResourceBaseTestCase):

    def setUp(self):
        cache.clear()
        self.target = ResourceItem.objects.create(
            title="Delete Target",
            description="<p>d</p>",
            grade=self.grade,
            learning_area=self.learning_area,
            file=make_pdf("del.pdf"),
            vendor=self.vendor,
            is_free=True,
            resource_type="notes",
        )

    def tearDown(self):
        cache.clear()

    def _url(self, slug=None):
        return reverse("resources:manage_delete",
                       kwargs={"slug": slug or self.target.slug})

    def test_anonymous_denied(self):
        r = self.client.post(self._url())
        self.assertIn(r.status_code, [302, 403])

    def test_vendor_can_delete_own_resource(self):
        self.login_as_vendor()
        self.client.post(self._url())
        self.assertFalse(ResourceItem.objects.filter(pk=self.target.pk).exists())

    def test_vendor_cannot_delete_others_resource(self):
        other = self.make_resource(title="Others Delete", vendor=self.admin)
        self.login_as_vendor()
        r = self.client.post(self._url(other.slug))
        self.assertEqual(r.status_code, 404)

    def test_admin_can_delete_any_resource(self):
        self.login_as_admin()
        self.client.post(self._url())
        self.assertFalse(ResourceItem.objects.filter(pk=self.target.pk).exists())

    def test_delete_redirects_to_dashboard(self):
        self.login_as_vendor()
        r = self.client.post(self._url())
        self.assertRedirects(r, reverse("accounts:dashboard"), fetch_redirect_response=False)
