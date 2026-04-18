from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from accounts.admin_views import IsAdminMixin
from cms.forms import MenuForm, SiteSettingForm, MenuItemForm
from cms.models import Page, Menu, SiteSetting, MenuItem


# ── CMS Pages ────────────────────────────────────────────────────────────────
class AdminPageListView(IsAdminMixin, ListView):
    model = Page
    template_name = "admin/page_list.html"
    context_object_name = "pages"


class AdminPageCreateView(IsAdminMixin, CreateView):
    model = Page
    template_name = "admin/seo_form.html"
    fields = ["title", "slug", "content", "is_published",
              "focus_keyword", "meta_title", "meta_description", "meta_keywords", "featured_image"]
    success_url = reverse_lazy("management:page_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New Page"
        ctx["cancel_url"] = self.success_url
        ctx["parent_title"] = "Pages"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Page created successfully.")
        return super().form_valid(form)


class AdminPageUpdateView(IsAdminMixin, UpdateView):
    model = Page
    template_name = "admin/seo_form.html"
    fields = ["title", "slug", "content", "is_published",
              "focus_keyword", "meta_title", "meta_description", "meta_keywords", "featured_image"]
    success_url = reverse_lazy("management:page_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Page: {self.object.title}"
        ctx["cancel_url"] = self.success_url
        ctx["parent_title"] = "Pages"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Page updated successfully.")
        return super().form_valid(form)


class AdminPageDeleteView(IsAdminMixin, DeleteView):
    model = Page
    success_url = reverse_lazy("management:page_list")

    def form_valid(self, form):
        messages.success(self.request, "Page permanently deleted.")
        return super().form_valid(form)


# ── CMS Menus ────────────────────────────────────────────────────────────────
class AdminMenuListView(IsAdminMixin, ListView):
    model = Menu
    template_name = "admin/menu_list.html"
    context_object_name = "menus"


class AdminMenuCreateView(IsAdminMixin, CreateView):
    model = Menu
    template_name = "admin/generic_form.html"
    form_class = MenuForm
    success_url = reverse_lazy("management:menu_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New Menu"
        ctx["cancel_url"] = self.success_url
        ctx["datalists"] = {
            "menu_names_list": [
                {"value": "primary_header", "label": "Main navigation at the top"},
                {"value": "footer", "label": "Quick links in the footer"},
            ]
        }
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Menu created.")
        return super().form_valid(form)


class AdminMenuUpdateView(IsAdminMixin, UpdateView):
    model = Menu
    template_name = "admin/generic_form.html"
    form_class = MenuForm
    success_url = reverse_lazy("management:menu_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Menu: {self.object.name}"
        ctx["cancel_url"] = self.success_url
        ctx["datalists"] = {
            "menu_names_list": [
                {"value": "primary_header", "label": "Main navigation at the top"},
                {"value": "footer", "label": "Quick links in the footer"},
            ]
        }
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Menu updated.")
        return super().form_valid(form)


class AdminMenuDeleteView(IsAdminMixin, DeleteView):
    model = Menu
    success_url = reverse_lazy("management:menu_list")

    def form_valid(self, form):
        messages.success(self.request, "Menu permanently deleted.")
        return super().form_valid(form)


# ── Menu Items ──────────────────────────────────────────────────────────────
class AdminMenuItemListView(IsAdminMixin, ListView):
    model = MenuItem
    template_name = "admin/basic_list.html"
    context_object_name = "items"
    extra_context = {
        "title": "Menu Items",
        "add_url": "management:menuitem_add",
        "edit_url": "management:menuitem_edit",
        "delete_url": "management:menuitem_delete",
        "columns": [("Title", "title"), ("Menu", "menu"), ("URL", "url"), ("Order", "order")]
    }


class AdminMenuItemCreateView(IsAdminMixin, CreateView):
    model = MenuItem
    template_name = "admin/generic_form.html"
    form_class = MenuItemForm
    success_url = reverse_lazy("management:menuitem_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Add Menu Item"
        ctx["datalists"] = {
            "menuitem_urls_list": [
                {"value": "/", "label": "Homepage"},
                {"value": "/resources/", "label": "All Resources"},
                {"value": "/contact/", "label": "Contact Page"},
                {"value": "/partners/", "label": "Partners"},
            ]
        }
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Menu Item created.")
        return super().form_valid(form)


class AdminMenuItemUpdateView(IsAdminMixin, UpdateView):
    model = MenuItem
    template_name = "admin/generic_form.html"
    form_class = MenuItemForm
    success_url = reverse_lazy("management:menuitem_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Edit Menu Item"
        ctx["datalists"] = {
            "menuitem_urls_list": [
                {"value": "/", "label": "Homepage"},
                {"value": "/resources/", "label": "All Resources"},
                {"value": "/contact/", "label": "Contact Page"},
                {"value": "/partners/", "label": "Partners"},
            ]
        }
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Menu Item updated.")
        return super().form_valid(form)


class AdminMenuItemDeleteView(IsAdminMixin, DeleteView):
    model = MenuItem
    success_url = reverse_lazy("management:menuitem_list")

    def form_valid(self, form):
        messages.success(self.request, "Deleted Menu Item.")
        return super().form_valid(form)


# ── Site Settings ────────────────────────────────────────────────────────────
class AdminSiteSettingsListView(IsAdminMixin, ListView):
    model = SiteSetting
    template_name = "admin/settings_list.html"
    context_object_name = "settings"


class AdminSiteSettingsCreateView(IsAdminMixin, CreateView):
    model = SiteSetting
    template_name = "admin/generic_form.html"
    form_class = SiteSettingForm
    success_url = reverse_lazy("management:settings_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New Setting"
        ctx["cancel_url"] = self.success_url
        ctx["datalists"] = {
            "setting_keys_list": [
                {"value": "site_name", "label": "Appears in title bar and headers"},
                {"value": "meta_description", "label": "Default fallback meta description for SEO"},
                {"value": "contact_email", "label": "Public support email address"},
                {"value": "contact_phone", "label": "Public contact phone number"},
                {"value": "social_facebook", "label": "Facebook page URL"},
                {"value": "social_twitter", "label": "Twitter profile URL"},
                {"value": "social_instagram", "label": "Instagram profile URL"},
                {"value": "google_oauth_client_id", "label": "Google OAuth Client ID for login"},
                {"value": "site_indexing", "label": "Toggle search engine indexing (true/false)"},
                {"value": "site_logo_url", "label": "Enter the full url of the site logo"},
            ]
        }
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Setting created.")
        return super().form_valid(form)


class AdminSiteSettingsUpdateView(IsAdminMixin, UpdateView):
    model = SiteSetting
    template_name = "admin/generic_form.html"
    form_class = SiteSettingForm
    success_url = reverse_lazy("management:settings_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Setting: {self.object.key}"
        ctx["cancel_url"] = self.success_url
        ctx["datalists"] = {
            "setting_keys_list": [
                {"value": "site_name", "label": "Appears in title bar and headers"},
                {"value": "meta_description", "label": "Default fallback meta description for SEO"},
                {"value": "contact_email", "label": "Public support email address"},
                {"value": "contact_phone", "label": "Public contact phone number"},
                {"value": "social_facebook", "label": "Facebook page URL"},
                {"value": "social_twitter", "label": "Twitter profile URL"},
                {"value": "social_instagram", "label": "Instagram profile URL"},
                {"value": "google_oauth_client_id", "label": "Google OAuth Client ID for login"},
                {"value": "site_indexing", "label": "Toggle search engine indexing (true/false)"},
            ]
        }
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Site setting updated.")
        return super().form_valid(form)


class AdminSiteSettingsDeleteView(IsAdminMixin, DeleteView):
    model = SiteSetting
    success_url = reverse_lazy("management:settings_list")

    def form_valid(self, form):
        messages.success(self.request, "Setting permanently deleted.")
        return super().form_valid(form)
