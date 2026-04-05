from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView, ListView, UpdateView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages

from accounts.models import CustomUser
from cms.models import Page, Menu, SiteSetting
from resources.models import ResourceItem

class IsAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.role == CustomUser.Role.ADMIN)

# ── Dashboard ────────────────────────────────────────────────────────────────
class AdminDashboardView(IsAdminMixin, TemplateView):
    template_name = "admin/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_users"] = CustomUser.objects.count()
        ctx["total_vendors"] = CustomUser.objects.filter(role=CustomUser.Role.VENDOR).count()
        ctx["total_resources"] = ResourceItem.objects.count()
        ctx["total_pages"] = Page.objects.count()
        
        ctx["recent_users"] = CustomUser.objects.order_by("-date_joined")[:5]
        ctx["recent_resources"] = ResourceItem.objects.select_related("vendor").order_by("-created_at")[:5]
        return ctx

# ── Users ────────────────────────────────────────────────────────────────────
class AdminUserListView(IsAdminMixin, ListView):
    model = CustomUser
    template_name = "admin/user_list.html"
    context_object_name = "users"
    paginate_by = 30

    def get_queryset(self):
        qs = CustomUser.objects.all().order_by("-date_joined")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(email__icontains=q)
        return qs

class AdminUserCreateView(IsAdminMixin, CreateView):
    model = CustomUser
    template_name = "admin/generic_form.html"
    fields = ["email", "first_name", "last_name", "is_active", "role", "is_vendor"]
    success_url = reverse_lazy("management:user_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New User"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        # We manually build the user so it hashes a default unusable password or similar,
        # but since we're using generic forms, we'll let it save directly if it's fine.
        # CustomUser uses email as unique.
        messages.success(self.request, "User created successfully.")
        return super().form_valid(form)

class AdminUserUpdateView(IsAdminMixin, UpdateView):
    model = CustomUser
    template_name = "admin/generic_form.html"
    fields = ["email", "first_name", "last_name", "is_active", "role", "is_vendor"]
    success_url = reverse_lazy("management:user_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit User: {self.object.email}"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "User updated successfully.")
        return super().form_valid(form)

# ── CMS Pages ────────────────────────────────────────────────────────────────
class AdminPageListView(IsAdminMixin, ListView):
    model = Page
    template_name = "admin/page_list.html"
    context_object_name = "pages"

class AdminPageCreateView(IsAdminMixin, CreateView):
    model = Page
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:page_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New Page"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Page created successfully.")
        return super().form_valid(form)

class AdminPageUpdateView(IsAdminMixin, UpdateView):
    model = Page
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:page_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Page: {self.object.title}"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Page updated successfully.")
        return super().form_valid(form)

class AdminPageDeleteView(IsAdminMixin, DeleteView):
    model = Page
    template_name = "resources/resource_confirm_delete.html" # Re-use confirmation layout visually
    success_url = reverse_lazy("management:page_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Delete Page?"
        ctx["cancel_url"] = self.success_url
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Page deleted automatically.")
        return super().delete(request, *args, **kwargs)

# ── CMS Menus ────────────────────────────────────────────────────────────────
class AdminMenuListView(IsAdminMixin, ListView):
    model = Menu
    template_name = "admin/menu_list.html"
    context_object_name = "menus"

class AdminMenuCreateView(IsAdminMixin, CreateView):
    model = Menu
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:menu_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New Menu"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Menu created.")
        return super().form_valid(form)

class AdminMenuUpdateView(IsAdminMixin, UpdateView):
    model = Menu
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:menu_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Menu: {self.object.name}"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Menu updated.")
        return super().form_valid(form)

# ── Site Settings ────────────────────────────────────────────────────────────
class AdminSiteSettingsListView(IsAdminMixin, ListView):
    model = SiteSetting
    template_name = "admin/settings_list.html"
    context_object_name = "settings"

class AdminSiteSettingsCreateView(IsAdminMixin, CreateView):
    model = SiteSetting
    template_name = "admin/generic_form.html"
    fields = ["key", "value"]
    success_url = reverse_lazy("management:settings_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New Setting"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Setting created.")
        return super().form_valid(form)

class AdminSiteSettingsUpdateView(IsAdminMixin, UpdateView):
    model = SiteSetting
    template_name = "admin/generic_form.html"
    fields = ["key", "value"]
    success_url = reverse_lazy("management:settings_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Setting: {self.object.key}"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Site setting updated.")
        return super().form_valid(form)

# ── Resources ────────────────────────────────────────────────────────────────
class AdminResourceListView(IsAdminMixin, ListView):
    model = ResourceItem
    template_name = "admin/resource_list.html"
    context_object_name = "resources"
    paginate_by = 30

    def get_queryset(self):
        qs = ResourceItem.objects.select_related("vendor", "grade", "learning_area").order_by("-created_at")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

class AdminResourceCreateView(IsAdminMixin, CreateView):
    model = ResourceItem
    template_name = "admin/generic_form.html"
    fields = ["title", "description", "grade", "learning_area", "file", "is_free", "price", "vendor"]
    success_url = reverse_lazy("management:resource_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New Resource"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Resource created successfully.")
        return super().form_valid(form)
