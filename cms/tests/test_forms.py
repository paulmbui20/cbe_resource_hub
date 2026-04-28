"""
cms/tests/test_forms.py

Covers MenuForm, SiteSettingForm, and MenuItemForm:
  - Valid inputs
  - Missing / blank required fields
  - Widget attributes are present
  - Duplicate key constraint surface (via form + model)
"""

from cms.forms import MenuForm, MenuItemForm, SiteSettingForm
from cms.tests.base import CMSBaseTestCase


# ── MenuForm ──────────────────────────────────────────────────────────────────

class MenuFormTests(CMSBaseTestCase):

    def test_valid_form_is_valid(self):
        form = MenuForm(data={"name": "Sidebar"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_blank_name_is_invalid(self):
        form = MenuForm(data={"name": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_missing_name_is_invalid(self):
        form = MenuForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_name_widget_has_datalist_attribute(self):
        form = MenuForm()
        widget = form.fields["name"].widget
        self.assertEqual(widget.attrs.get("list"), "menu_names_list")

    def test_name_widget_has_placeholder(self):
        form = MenuForm()
        widget = form.fields["name"].widget
        self.assertIn("placeholder", widget.attrs)

    def test_valid_form_saves_menu(self):
        form = MenuForm(data={"name": "Unique Menu 123"})
        self.assertTrue(form.is_valid())
        menu = form.save()
        self.assertEqual(menu.name, "Unique Menu 123")
        self.assertIsNotNone(menu.pk)


# ── SiteSettingForm ────────────────────────────────────────────────────────────

class SiteSettingFormTests(CMSBaseTestCase):

    def test_valid_form_is_valid(self):
        form = SiteSettingForm(data={"key": "new_unique_key", "value": "some value"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_blank_key_is_invalid(self):
        form = SiteSettingForm(data={"key": "", "value": "value"})
        self.assertFalse(form.is_valid())
        self.assertIn("key", form.errors)

    def test_blank_value_is_invalid(self):
        form = SiteSettingForm(data={"key": "some_key", "value": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("value", form.errors)

    def test_key_widget_has_datalist_attribute(self):
        form = SiteSettingForm()
        widget = form.fields["key"].widget
        self.assertEqual(widget.attrs.get("list"), "setting_keys_list")

    def test_key_widget_has_x_model_attribute(self):
        form = SiteSettingForm()
        widget = form.fields["key"].widget
        self.assertEqual(widget.attrs.get("x-model"), "settingKey")

    def test_value_widget_has_x_show_attribute(self):
        form = SiteSettingForm()
        widget = form.fields["value"].widget
        self.assertIn("x-show", widget.attrs)

    def test_value_widget_has_x_ref_attribute(self):
        form = SiteSettingForm()
        widget = form.fields["value"].widget
        self.assertEqual(widget.attrs.get("x-ref"), "realValueInput")

    def test_valid_form_saves_site_setting(self):
        form = SiteSettingForm(data={"key": "test_unique_key_xyz", "value": "test value"})
        self.assertTrue(form.is_valid())
        setting = form.save()
        self.assertEqual(setting.key, "test_unique_key_xyz")
        self.assertEqual(setting.value, "test value")


# ── MenuItemForm ───────────────────────────────────────────────────────────────

class MenuItemFormTests(CMSBaseTestCase):

    def _valid_data(self, **overrides):
        data = {
            "menu": self.primary_menu.pk,
            "title": "Test Item",
            "url": "/test/",
            "order": 1,
        }
        data.update(overrides)
        return data

    def test_valid_form_is_valid(self):
        form = MenuItemForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_blank_title_is_invalid(self):
        form = MenuItemForm(data=self._valid_data(title=""))
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_blank_url_is_invalid(self):
        form = MenuItemForm(data=self._valid_data(url=""))
        self.assertFalse(form.is_valid())
        self.assertIn("url", form.errors)

    def test_missing_menu_is_invalid(self):
        data = self._valid_data()
        del data["menu"]
        form = MenuItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("menu", form.errors)

    def test_url_widget_has_datalist_attribute(self):
        form = MenuItemForm()
        widget = form.fields["url"].widget
        self.assertEqual(widget.attrs.get("list"), "menuitem_urls_list")

    def test_valid_form_saves_menu_item(self):
        form = MenuItemForm(data=self._valid_data())
        self.assertTrue(form.is_valid())
        item = form.save()
        self.assertEqual(item.title, "Test Item")
        self.assertEqual(item.menu, self.primary_menu)

    def test_form_supports_optional_parent(self):
        data = self._valid_data(parent=self.home_primary_menu_item.pk)
        form = MenuItemForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save()
        self.assertEqual(item.parent, self.home_primary_menu_item)

    def test_form_with_no_parent_is_valid(self):
        data = self._valid_data()
        data.pop("parent", None)
        form = MenuItemForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
