"""
cms/tests/test_admin_views.py

Covers all admin views in cms/admin_views.py:
  - Access control: anonymous, user, vendor → denied; admin → allowed
  - Page CRUD: list, create, update, delete
  - Menu CRUD: list, create, update, delete
  - MenuItem CRUD: list, create, update, delete
  - SiteSetting CRUD: list, create, update, delete
"""

from django.urls import reverse

from accounts.models import CustomUser
from cms.models import Menu, MenuItem, Page, SiteSetting
from cms.tests.base import CMSBaseTestCase


# ── Shared base for admin view tests ─────────────────────────────────────────

class CMSAdminBaseTestCase(CMSBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = CustomUser.objects.create_superuser(
            email="cms_admin@example.com", password="pass123"
        )
        cls.regular_user = CustomUser.objects.create_user(
            email="cms_user@example.com", password="pass123"
        )
        cls.vendor = CustomUser.objects.create_user(
            email="cms_vendor@example.com",
            password="pass123",
            role=CustomUser.Role.VENDOR,
            is_vendor=True,
        )

    def login_as_admin(self):
        self.client.force_login(self.admin)

    def login_as_user(self):
        self.client.force_login(self.regular_user)

    def login_as_vendor(self):
        self.client.force_login(self.vendor)


# ── Access Control (IsAdminMixin) ─────────────────────────────────────────────

class CMSAccessControlTests(CMSAdminBaseTestCase):
    """Anonymous / regular user / vendor must be denied from every CMS admin view."""

    PROTECTED_GETS = [
        ("management:page_list", {}),
        ("management:page_add", {}),
        ("management:menu_list", {}),
        ("management:menu_add", {}),
        ("management:menuitem_list", {}),
        ("management:menuitem_add", {}),
        ("management:settings_list", {}),
        ("management:settings_add", {}),
    ]

    def _get(self, name, kwargs=None):
        return self.client.get(reverse(name, kwargs=kwargs))

    def test_anonymous_denied_page_list(self):
        r = self._get("management:page_list")
        self.assertIn(r.status_code, [302, 403])

    def test_regular_user_denied_page_list(self):
        self.login_as_user()
        r = self._get("management:page_list")
        self.assertIn(r.status_code, [302, 403])

    def test_vendor_denied_page_list(self):
        self.login_as_vendor()
        r = self._get("management:page_list")
        self.assertIn(r.status_code, [302, 403])

    def test_admin_allowed_page_list(self):
        self.login_as_admin()
        r = self._get("management:page_list")
        self.assertEqual(r.status_code, 200)

    def test_anonymous_denied_menu_list(self):
        r = self._get("management:menu_list")
        self.assertIn(r.status_code, [302, 403])

    def test_admin_allowed_menu_list(self):
        self.login_as_admin()
        r = self._get("management:menu_list")
        self.assertEqual(r.status_code, 200)

    def test_anonymous_denied_settings_list(self):
        r = self._get("management:settings_list")
        self.assertIn(r.status_code, [302, 403])

    def test_admin_allowed_settings_list(self):
        self.login_as_admin()
        r = self._get("management:settings_list")
        self.assertEqual(r.status_code, 200)


# ── Page CRUD ─────────────────────────────────────────────────────────────────

class AdminPageListViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:page_list")

    def test_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(self.url), "admin/page_list.html")

    def test_context_has_pages(self):
        self.assertIn("pages", self.client.get(self.url).context)

    def test_published_page_in_list(self):
        pages = list(self.client.get(self.url).context["pages"])
        slugs = [p.slug for p in pages]
        self.assertIn(self.page.slug, slugs)


class AdminPageCreateViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:page_add")

    def _payload(self, **kw):
        data = {
            "title": "New Admin Page",
            "slug": "new-admin-page",
            "content": "<p>Content</p>",
            "is_published": True,
            "focus_keyword": "",
            "meta_title": "",
            "meta_description": "",
            "meta_keywords": "",
        }
        data.update(kw)
        return data

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_get_uses_seo_form_template(self):
        self.assertTemplateUsed(self.client.get(self.url), "admin/seo_form.html")

    def test_context_has_title(self):
        self.assertIn("title", self.client.get(self.url).context)

    def test_valid_post_creates_page(self):
        self.client.post(self.url, data=self._payload())
        self.assertTrue(Page.objects.filter(slug="new-admin-page").exists())

    def test_valid_post_redirects_to_page_list(self):
        r = self.client.post(self.url, data=self._payload())
        self.assertRedirects(r, reverse("management:page_list"))

    def test_invalid_post_missing_title_re_renders(self):
        r = self.client.post(self.url, data=self._payload(title=""))
        self.assertEqual(r.status_code, 200)

    def test_invalid_post_missing_content_re_renders(self):
        r = self.client.post(self.url, data=self._payload(content=""))
        self.assertEqual(r.status_code, 200)

    def test_valid_post_with_seo_fields_saves_them(self):
        self.client.post(self.url, data=self._payload(
            slug="seo-page-99",
            focus_keyword="django cms",
            meta_title="SEO Title",
            meta_keywords="cms, django",
        ))
        page = Page.objects.get(slug="seo-page-99")
        self.assertEqual(page.focus_keyword, "django cms")
        self.assertEqual(page.meta_title, "SEO Title")


class AdminPageUpdateViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = Page.objects.create(
            title="Editable Page", slug="editable-page",
            content="<p>Old</p>", is_published=False
        )
        self.url = reverse("management:page_edit", kwargs={"pk": self.target.pk})

    def _payload(self, **kw):
        data = {
            "title": "Updated Title",
            "slug": self.target.slug,
            "content": "<p>Updated</p>",
            "is_published": True,
            "focus_keyword": "",
            "meta_title": "",
            "meta_description": "",
            "meta_keywords": "",
        }
        data.update(kw)
        return data

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_title_contains_page_title(self):
        r = self.client.get(self.url)
        self.assertIn(self.target.title, r.context["title"])

    def test_valid_post_updates_page(self):
        self.client.post(self.url, data=self._payload())
        self.target.refresh_from_db()
        self.assertEqual(self.target.title, "Updated Title")
        self.assertTrue(self.target.is_published)

    def test_valid_post_redirects_to_page_list(self):
        r = self.client.post(self.url, data=self._payload())
        self.assertRedirects(r, reverse("management:page_list"))

    def test_invalid_post_blank_title_re_renders(self):
        r = self.client.post(self.url, data=self._payload(title=""))
        self.assertEqual(r.status_code, 200)

    def test_nonexistent_page_returns_404(self):
        url = reverse("management:page_edit", kwargs={"pk": 99999})
        self.assertEqual(self.client.get(url).status_code, 404)


class AdminPageDeleteViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = Page.objects.create(
            title="Delete Me", slug="delete-me-page", content="<p>x</p>"
        )
        self.url = reverse("management:page_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_page(self):
        self.client.post(self.url)
        self.assertFalse(Page.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects_to_page_list(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:page_list"))

    def test_delete_nonexistent_page_returns_404(self):
        r = self.client.post(reverse("management:page_delete", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)


# ── Menu CRUD ─────────────────────────────────────────────────────────────────

class AdminMenuListViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        r = self.client.get(reverse("management:menu_list"))
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:menu_list")), "admin/menu_list.html"
        )

    def test_context_has_menus(self):
        r = self.client.get(reverse("management:menu_list"))
        self.assertIn("menus", r.context)


class AdminMenuCreateViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:menu_add")

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_has_datalists(self):
        r = self.client.get(self.url)
        self.assertIn("datalists", r.context)

    def test_valid_post_creates_menu(self):
        self.client.post(self.url, data={"name": "Sidebar Nav"})
        self.assertTrue(Menu.objects.filter(name="Sidebar Nav").exists())

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={"name": "Sidebar Nav 2"})
        self.assertRedirects(r, reverse("management:menu_list"))

    def test_blank_name_re_renders_form(self):
        r = self.client.post(self.url, data={"name": ""})
        self.assertEqual(r.status_code, 200)


class AdminMenuUpdateViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = Menu.objects.create(name="Old Menu Name")
        self.url = reverse("management:menu_edit", kwargs={"pk": self.target.pk})

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_title_contains_menu_name(self):
        r = self.client.get(self.url)
        self.assertIn(self.target.name, r.context["title"])

    def test_valid_post_updates_menu(self):
        self.client.post(self.url, data={"name": "Updated Menu Name"})
        self.target.refresh_from_db()
        self.assertEqual(self.target.name, "Updated Menu Name")

    def test_nonexistent_menu_returns_404(self):
        url = reverse("management:menu_edit", kwargs={"pk": 99999})
        self.assertEqual(self.client.get(url).status_code, 404)


class AdminMenuDeleteViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = Menu.objects.create(name="Menu To Delete")
        self.url = reverse("management:menu_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_menu(self):
        self.client.post(self.url)
        self.assertFalse(Menu.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:menu_list"))

    def test_cascades_to_menu_items(self):
        MenuItem.objects.create(
            menu=self.target, title="Child", url="/child/"
        )
        self.client.post(self.url)
        self.assertFalse(MenuItem.objects.filter(menu=self.target).exists())


# ── MenuItem CRUD ─────────────────────────────────────────────────────────────

class AdminMenuItemListViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        r = self.client.get(reverse("management:menuitem_list"))
        self.assertEqual(r.status_code, 200)

    def test_context_has_items(self):
        r = self.client.get(reverse("management:menuitem_list"))
        self.assertIn("items", r.context)


class AdminMenuItemCreateViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:menuitem_add")

    def _payload(self, **kw):
        data = {
            "menu": self.primary_menu.pk,
            "title": "New Nav Item",
            "url": "/new/",
            "order": 5,
        }
        data.update(kw)
        return data

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_has_datalists(self):
        self.assertIn("datalists", self.client.get(self.url).context)

    def test_valid_post_creates_item(self):
        self.client.post(self.url, data=self._payload())
        self.assertTrue(MenuItem.objects.filter(title="New Nav Item").exists())

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data=self._payload(title="Nav Item 2"))
        self.assertRedirects(r, reverse("management:menuitem_list"))

    def test_blank_title_re_renders(self):
        r = self.client.post(self.url, data=self._payload(title=""))
        self.assertEqual(r.status_code, 200)

    def test_blank_url_re_renders(self):
        r = self.client.post(self.url, data=self._payload(url=""))
        self.assertEqual(r.status_code, 200)


class AdminMenuItemUpdateViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = MenuItem.objects.create(
            menu=self.primary_menu, title="Old Item", url="/old/"
        )
        self.url = reverse("management:menuitem_edit", kwargs={"pk": self.target.pk})

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_updates_item(self):
        self.client.post(self.url, data={
            "menu": self.primary_menu.pk,
            "title": "Updated Item",
            "url": "/updated/",
            "order": 2,
        })
        self.target.refresh_from_db()
        self.assertEqual(self.target.title, "Updated Item")

    def test_nonexistent_item_returns_404(self):
        url = reverse("management:menuitem_edit", kwargs={"pk": 99999})
        self.assertEqual(self.client.get(url).status_code, 404)


class AdminMenuItemDeleteViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = MenuItem.objects.create(
            menu=self.primary_menu, title="Delete Item", url="/del/"
        )
        self.url = reverse("management:menuitem_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_item(self):
        self.client.post(self.url)
        self.assertFalse(MenuItem.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:menuitem_list"))


# ── SiteSetting CRUD ──────────────────────────────────────────────────────────

class AdminSiteSettingsListViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()

    def test_returns_200(self):
        r = self.client.get(reverse("management:settings_list"))
        self.assertEqual(r.status_code, 200)

    def test_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse("management:settings_list")),
            "admin/settings_list.html",
        )

    def test_context_has_settings(self):
        r = self.client.get(reverse("management:settings_list"))
        self.assertIn("settings", r.context)


class AdminSiteSettingsCreateViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.url = reverse("management:settings_add")

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_has_datalists(self):
        self.assertIn("datalists", self.client.get(self.url).context)

    def test_valid_post_creates_setting(self):
        self.client.post(self.url, data={"key": "new_unique_setting", "value": "val"})
        self.assertTrue(SiteSetting.objects.filter(key="new_unique_setting").exists())

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={"key": "another_setting", "value": "v"})
        self.assertRedirects(r, reverse("management:settings_list"))

    def test_blank_key_re_renders(self):
        r = self.client.post(self.url, data={"key": "", "value": "v"})
        self.assertEqual(r.status_code, 200)


class AdminSiteSettingsUpdateViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = SiteSetting.objects.create(key="editable_key", value="old value")
        self.url = reverse("management:settings_edit", kwargs={"pk": self.target.pk})

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_title_contains_key(self):
        r = self.client.get(self.url)
        self.assertIn(self.target.key, r.context["title"])

    def test_valid_post_updates_value(self):
        self.client.post(self.url, data={"key": "editable_key", "value": "new value"})
        self.target.refresh_from_db()
        self.assertEqual(self.target.value, "new value")

    def test_valid_post_redirects(self):
        r = self.client.post(self.url, data={"key": "editable_key", "value": "v2"})
        self.assertRedirects(r, reverse("management:settings_list"))

    def test_nonexistent_setting_returns_404(self):
        url = reverse("management:settings_edit", kwargs={"pk": 99999})
        self.assertEqual(self.client.get(url).status_code, 404)


class AdminSiteSettingsDeleteViewTests(CMSAdminBaseTestCase):
    def setUp(self):
        self.login_as_admin()
        self.target = SiteSetting.objects.create(key="delete_me_key", value="x")
        self.url = reverse("management:settings_delete", kwargs={"pk": self.target.pk})

    def test_post_deletes_setting(self):
        self.client.post(self.url)
        self.assertFalse(SiteSetting.objects.filter(pk=self.target.pk).exists())

    def test_post_redirects(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("management:settings_list"))

    def test_delete_nonexistent_returns_404(self):
        r = self.client.post(reverse("management:settings_delete", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)
