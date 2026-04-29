from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils.html import strip_tags

from cms.models import Page, SiteSetting, Menu, MenuItem
from cms.tests.base import CMSBaseTestCase


class TestCMSPageCreation(CMSBaseTestCase):

    def test_page_creation(self):
        self.assertIsNotNone(self.page)
        self.assertEqual(self.page.slug, 'page-title')
        self.assertEqual(self.page.title, 'Page title')
        self.assertEqual(self.page.content, '<h2>Page content</h2>')
        self.assertEqual(self.page.is_published, True)

    def test_page_creation_with_meta_title(self):
        self.assertEqual(self.page.title, self.page.meta_title)

    def test_page_creation_with_meta_description(self):
        self.assertEqual(self.page.meta_description, strip_tags(self.page.content))

    def test_page_creation_with_slug_generation(self):
        self.page2 = Page.objects.create(
            title="Page title2",
            slug="",
        )
        self.assertEqual(self.page2.slug, 'page-title2')

    def test_page_creation_with_non_unique_slug(self):
        self.page3 = Page.objects.create(
            title="Page title",
            slug="",
        )
        self.assertEqual(self.page3.slug, 'page-title-1')
        self.page4 = Page.objects.create(
            title="Page title",
            slug="",
        )
        self.assertEqual(self.page4.slug, 'page-title-2')

    def test_page_is_saved_with_is_published_as_false_by_default(self):
        self.page4 = Page.objects.create(
            title="Page title 4",
        )
        self.assertEqual(self.page4.is_published, False)

    def test_page_creation_with_duplicate_slug_throws_integrity_error(self):
        with self.assertRaises(IntegrityError):
            Page.objects.create(
                title="Page title 5",
                slug="page-title",
            )

    def test_page_creation_without_title_raises_error(self):
        with self.assertRaises(IntegrityError):
            Page.objects.create(
                title=None,
                slug="no-title-page",
            )

    def test_page_update_without_title_raises_error(self):
        with self.assertRaises(IntegrityError):
            Page.objects.filter(pk=self.page.pk).update(
                title=None,
            )

    def test_page_update_without_slug_raises_error(self):
        with self.assertRaises(IntegrityError):
            Page.objects.filter(pk=self.page.pk).update(
                slug=None,
            )

    def test_page_create_without_content_raises_error(self):
        with self.assertRaises(IntegrityError):
            Page.objects.create(
                title="No Content Page",
                content=None,
            )

    def test_page_update_without_content_raises_error(self):
        with self.assertRaises(IntegrityError):
            Page.objects.filter(pk=self.page.pk).update(
                content=None,
            )

    def test_page_create_without_is_published_raises_error(self):
        with self.assertRaises(IntegrityError):
            Page.objects.create(
                title="No is_published Page",
                is_published=None,
            )

    def test_page_create_with_title_longer_than_field_input_size_raises_value_error_on_full_clean(self):
        with self.assertRaises(ValidationError):
            Page.objects.create(
                title=self.long_title("t", 300)
            ).full_clean()

    def test_page_create_with_slug_longer_than_field_input_size_raises_value_error_on_full_clean(self):
        with self.assertRaises(ValidationError):
            Page.objects.create(
                title=self.long_title("t", 100),
                slug=self.long_title("t", 300)
            ).full_clean()


class TestCMSSiteSettingsCreation(CMSBaseTestCase):

    def test_create_site_name_site_setting(self):
        self.assertIsNotNone(self.site_name_site_setting)

    def test_create_site_indexing_site_setting(self):
        self.assertIsNotNone(self.site_indexing_site_setting)

    def test_create_contact_phone_site_setting(self):
        self.assertIsNotNone(self.contact_phone_site_setting)

    def test_create_contact_email_site_setting(self):
        self.assertIsNotNone(self.contact_email_site_setting)

    def test_create_meta_description_site_setting(self):
        self.assertIsNotNone(self.meta_description_site_setting)

    def test_create_meta_keywords_site_setting(self):
        self.assertIsNotNone(self.meta_keywords_site_setting)

    def test_create_site_setting_with_duplicate_key_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            SiteSetting.objects.create(
                key="site_name",
                value="Test Duplicate key",
            )

    def test_create_site_setting_with_duplicate_key_but_different_casing_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            SiteSetting.objects.create(
                key="SITE_NAME",
                value="Test Duplicate key",
            )

    def test_create_site_setting_with_no_value_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            SiteSetting.objects.create(
                key="no_value",
                value=None,
            )

    def test_update_site_setting_with_no_value_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            SiteSetting.objects.filter(pk=self.site_name_site_setting.pk).update(
                value=None,
            )

    def test_create_site_setting_with_no_key_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            SiteSetting.objects.create(
                key=None,
                value="no key"
            )

    def test_update_site_setting_with_no_key_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            SiteSetting.objects.filter(pk=self.site_name_site_setting.pk).update(
                key=None,
            )

    def test_create_site_setting_with_key_longer_than_max_length_raises_validation_error_on_full_clean(self):
        with self.assertRaises(ValidationError):
            SiteSetting.objects.create(
                key=self.long_title("t", 60),
            ).full_clean()


class TestCMSMenuCreation(CMSBaseTestCase):

    def test_create_primary_menu(self):
        self.assertIsNotNone(self.primary_menu)

    def test_create_footer_menu(self):
        self.assertIsNotNone(self.footer_menu)

    def test_create_menu_with_duplicate_name_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            Menu.objects.create(
                name="Primary Header"
            )

    def test_create_menu_with_duplicate_name_but_different_casing_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            Menu.objects.create(
                name="footer"
            )

    def test_update_menu_with_duplicate_name_but_different_casing_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            Menu.objects.create(
                name="DUPLICATE"
            )
            Menu.objects.create(
                name="duplicate1"
            )
            Menu.objects.filter(name="duplicate1").update(
                name="DUPLICATE"
            )

    def test_create_menu_with_no_name_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            Menu.objects.create(
                name=None
            )

    def test_create_menu_with_name_longer_than_max_length_raises_validation_error_on_full_clean(self):
        with self.assertRaises(ValidationError):
            Menu.objects.create(
                name=self.long_title("t", 60),
            ).full_clean()


class TestCMSMenuItemsCreation(CMSBaseTestCase):

    def test_create_primary_menu_item(self):
        self.assertIsNotNone(self.home_primary_menu_item.pk)

    def test_create_footer_menu_item(self):
        self.assertIsNotNone(self.partners_footer_menu_item.pk)

    def test_create_menu_item_with_no_menu_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            MenuItem.objects.create(
                menu=None,
                title="No menu",
                url="https://example.com",
            )

    def test_update_menu_item_with_no_menu_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            MenuItem.objects.filter(pk=self.partners_footer_menu_item.pk).update(
                menu=None,
            )

    def test_create_menu_item_with_no_title_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            MenuItem.objects.create(
                menu=self.primary_menu,
                title=None,
                url="https://example.com",
            )

    def test_update_menu_item_with_no_title_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            MenuItem.objects.filter(pk=self.home_primary_menu_item.pk).update(
                title=None,
            )

    def test_create_menu_item_with_no_url_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            MenuItem.objects.create(
                menu=self.primary_menu,
                title="No URL",
                url=None,
            )

    def test_update_menu_item_with_no_url_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            MenuItem.objects.filter(pk=self.home_primary_menu_item.pk).update(
                url=None,
            )

    def test_create_menu_item_with_null_order_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            MenuItem.objects.create(
                menu=self.primary_menu,
                title="Null Order",
                url="https://example.com",
                order=None,
            )

    def test_update_menu_item_with_null_order_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            MenuItem.objects.filter(pk=self.home_primary_menu_item.pk).create(
                order=None,
            )

    def test_create_menu_item_with_title_longer_than_max_length_raises_validation_error_on_full_clean(self):
        with self.assertRaises(ValidationError):
            MenuItem.objects.create(
                menu=self.primary_menu,
                title=self.long_title("t", 110),
                url="https://example.com",
            ).full_clean()

    def test_create_menu_item_with_url_longer_than_max_length_raises_validation_error_on_full_clean(self):
        with self.assertRaises(ValidationError):
            MenuItem.objects.create(
                menu=self.primary_menu,
                title="Long URL",
                url=f"https://{self.long_title("u", 500)}.com",
            ).full_clean()
