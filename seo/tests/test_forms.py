"""
seo/tests/test_forms.py

Tests for SlugRedirectForm:
  - Valid data is accepted
  - Both fields are required
  - Widget types and CSS class attributes
  - Help texts present
"""

from django.test import TestCase

from seo.forms import SlugRedirectForm


class SlugRedirectFormTests(TestCase):

    def _valid_data(self, **overrides):
        data = {"old_slug": "old-page", "new_slug": "new-page"}
        data.update(overrides)
        return data

    # ── Validity ──────────────────────────────────────────────────────────────

    def test_valid_form_is_valid(self):
        form = SlugRedirectForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_old_slug_is_invalid(self):
        form = SlugRedirectForm(data=self._valid_data(old_slug=""))
        self.assertFalse(form.is_valid())
        self.assertIn("old_slug", form.errors)

    def test_missing_new_slug_is_invalid(self):
        form = SlugRedirectForm(data=self._valid_data(new_slug=""))
        self.assertFalse(form.is_valid())
        self.assertIn("new_slug", form.errors)

    # ── Widgets ───────────────────────────────────────────────────────────────

    def test_old_slug_widget_is_textarea(self):
        from django import forms as dj_forms
        form = SlugRedirectForm()
        self.assertIsInstance(form.fields["old_slug"].widget, dj_forms.Textarea)

    def test_new_slug_widget_is_textarea(self):
        from django import forms as dj_forms
        form = SlugRedirectForm()
        self.assertIsInstance(form.fields["new_slug"].widget, dj_forms.Textarea)

    def test_old_slug_widget_has_class(self):
        form = SlugRedirectForm()
        self.assertIn("class", form.fields["old_slug"].widget.attrs)

    def test_new_slug_widget_has_class(self):
        form = SlugRedirectForm()
        self.assertIn("class", form.fields["new_slug"].widget.attrs)

    # ── Fields ────────────────────────────────────────────────────────────────

    def test_form_has_old_slug_field(self):
        form = SlugRedirectForm()
        self.assertIn("old_slug", form.fields)

    def test_form_has_new_slug_field(self):
        form = SlugRedirectForm()
        self.assertIn("new_slug", form.fields)

    def test_form_only_has_expected_fields(self):
        form = SlugRedirectForm()
        self.assertEqual(set(form.fields.keys()), {"old_slug", "new_slug"})

    # ── Save ──────────────────────────────────────────────────────────────────

    def test_valid_form_saves_redirect(self):
        from django.contrib.contenttypes.models import ContentType
        from resources.models import EducationLevel
        form = SlugRedirectForm(data=self._valid_data(old_slug="form-old", new_slug="form-new"))
        self.assertTrue(form.is_valid())
        redirect = form.save(commit=False)
        # Manually assign required GenericFK fields before full save
        ct = ContentType.objects.get_for_model(EducationLevel)
        redirect.content_type = ct
        redirect.object_id = 1
        redirect.save()
        from seo.models import SlugRedirect
        self.assertTrue(SlugRedirect.objects.filter(old_slug="form-old").exists())
