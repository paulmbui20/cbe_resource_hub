from django.test import TestCase

from cms.models import Page, SiteSetting, Menu, MenuItem


class CMSBaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page = Page.objects.create(
            title="Page title",
            slug="page-title",
            content="<h2>Page content</h2>",
            is_published=True,
        )
        cls.site_name_site_setting = SiteSetting.objects.create(
            key="site_name",
            value="Test Site Name",
        )
        cls.site_indexing_site_setting = SiteSetting.objects.create(
            key="site_indexing",
            value="true"
        )
        cls.contact_phone_site_setting = SiteSetting.objects.create(
            key="contact_phone",
            value="+254712345678"
        )
        cls.contact_email_site_setting = SiteSetting.objects.create(
            key="contact_email",
            value="contact@example.com"
        )
        cls.meta_description_site_setting = SiteSetting.objects.create(
            key="meta_description",
            value="Test meta description"
        )
        cls.meta_keywords_site_setting = SiteSetting.objects.create(
            key="meta_keywords",
            value="keyword 1, keyword 2, keyword 3"
        )
        cls.primary_menu = Menu.objects.create(
            name="Primary Header",
        )
        cls.footer_menu = Menu.objects.create(
            name="Footer",
        )
        cls.home_primary_menu_item = MenuItem.objects.create(
            menu=cls.primary_menu,
            title="Home",
            url="/",
        )
        cls.partners_footer_menu_item = MenuItem.objects.create(
            menu=cls.footer_menu,
            title="Partners",
            url="/partners/",
        )

    def long_title(self, characters: str ,length: int) -> str:
        long_title = characters * length
        return long_title


