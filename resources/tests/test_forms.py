"""
resources/tests/test_forms.py

Tests for ResourceItemForm:
  - Valid data creates a ResourceItem
  - Required fields enforced
  - Widget class attributes present
  - is_free / price coupling reflected in saved record
"""

from resources.forms import ResourceItemForm
from resources.tests.base import ResourceBaseTestCase, make_pdf


class ResourceItemFormTests(ResourceBaseTestCase):
    def _base_data(self, **overrides):
        data = {
            "title": "Form Test Resource",
            "resource_type": "notes",
            "description": "<p>Content here</p>",
            "grade": self.grade.pk,
            "learning_area": self.learning_area.pk,
            "academic_session": self.session.pk,
            "is_free": True,
        }
        data.update(overrides)
        return data

    def _files(self, filename="upload.pdf"):
        return {"file": make_pdf(filename)}

    # ── Validity ──────────────────────────────────────────────────────────────

    def test_valid_form_is_valid(self):
        form = ResourceItemForm(data=self._base_data(), files=self._files())
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_title_is_invalid(self):
        form = ResourceItemForm(data=self._base_data(title=""), files=self._files())
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_missing_description_is_valid(self):
        form = ResourceItemForm(
            data=self._base_data(description=""),
            files=self._files(filename="no_desc.pdf"),
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_grade_is_invalid(self):
        data = self._base_data()
        data.pop("grade")
        form = ResourceItemForm(data=data, files=self._files())
        self.assertFalse(form.is_valid())
        self.assertIn("grade", form.errors)

    def test_missing_learning_area_is_invalid(self):
        data = self._base_data()
        data.pop("learning_area")
        form = ResourceItemForm(data=data, files=self._files())
        self.assertFalse(form.is_valid())
        self.assertIn("learning_area", form.errors)

    def test_missing_file_is_invalid(self):
        form = ResourceItemForm(data=self._base_data(), files={})
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_academic_session_optional(self):
        data = self._base_data()
        data.pop("academic_session")
        form = ResourceItemForm(data=data, files=self._files(filename="opt.pdf"))
        self.assertTrue(form.is_valid(), form.errors)

    # ── Save ──────────────────────────────────────────────────────────────────

    def test_valid_form_saves_resource(self):
        form = ResourceItemForm(
            data=self._base_data(), files=self._files(filename="save.pdf")
        )
        self.assertTrue(form.is_valid(), form.errors)
        resource = form.save()
        self.assertIsNotNone(resource.pk)
        self.assertEqual(resource.title, "Form Test Resource")

    def test_is_free_true_sets_zero_price(self):
        form = ResourceItemForm(
            data=self._base_data(is_free=True),
            files=self._files(filename="free.pdf"),
        )
        self.assertTrue(form.is_valid())
        resource = form.save()
        resource.refresh_from_db()
        self.assertEqual(float(resource.price), 0.0)

    # ── Widget Attributes ─────────────────────────────────────────────────────

    def test_title_widget_has_class(self):
        form = ResourceItemForm()
        self.assertIn("class", form.fields["title"].widget.attrs)

    def test_grade_widget_is_select(self):
        from django import forms as dj_forms

        form = ResourceItemForm()
        self.assertIsInstance(form.fields["grade"].widget, dj_forms.Select)

    def test_learning_area_widget_is_select(self):
        from django import forms as dj_forms

        form = ResourceItemForm()
        self.assertIsInstance(form.fields["learning_area"].widget, dj_forms.Select)

    def test_is_free_widget_is_checkbox(self):
        from django import forms as dj_forms

        form = ResourceItemForm()
        self.assertIsInstance(form.fields["is_free"].widget, dj_forms.CheckboxInput)

    # ── Fields Present ────────────────────────────────────────────────────────

    def test_all_expected_fields_present(self):
        form = ResourceItemForm()
        for field in [
            "title",
            "resource_type",
            "description",
            "grade",
            "learning_area",
            "academic_session",
            "file",
            "is_free",
        ]:
            self.assertIn(field, form.fields, f"Field '{field}' missing from form")

    def test_price_field_not_in_form(self):
        """price is deliberately excluded."""
        form = ResourceItemForm()
        self.assertNotIn("price", form.fields)
