from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import TemplateView, ListView, UpdateView, CreateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages

from accounts.models import CustomUser
from cms.models import Page, Menu, SiteSetting
from resources.models import ResourceItem
from website.models import ContactMessage, Partner
from notifications.admin_views import AdminNotificationListView, AdminNotificationRetryView

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
        ctx["unread_messages"] = ContactMessage.objects.filter(is_read=False).count()

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
        import secrets
        import string
        from django.contrib import messages
        
        user = form.save(commit=False)
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        raw_password = "".join(secrets.choice(alphabet) for i in range(12))
        
        user.set_password(raw_password)
        user.must_change_password = True
        user.save()
        
        messages.success(self.request, f"User created securely! Their generated password is: {raw_password}")
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

class AdminUserDeleteView(IsAdminMixin, DeleteView):
    model = CustomUser
    success_url = reverse_lazy("management:user_list")
    
    def form_valid(self, form):
        messages.success(self.request, "User permanently deleted.")
        return super().form_valid(form)

from django.http import JsonResponse
import json

class AdminUserBulkToggleView(IsAdminMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            action = data.get("action")
            user_ids = data.get("user_ids", [])
            
            if action not in ["enable", "disable"] or not user_ids:
                return JsonResponse({"error": "Invalid request"}, status=400)
            
            # Guard against disabling self
            if action == "disable" and str(request.user.id) in [str(u) for u in user_ids]:
                return JsonResponse({"error": "You cannot disable your own account."}, status=403)
                
            is_active_val = (action == "enable")
            updated = CustomUser.objects.filter(id__in=user_ids).update(is_active=is_active_val)
            messages.success(request, f"Successfully {action}d {updated} users.")
            return JsonResponse({"success": True})
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

# ── CMS Pages ────────────────────────────────────────────────────────────────
class AdminPageListView(IsAdminMixin, ListView):
    model = Page
    template_name = "admin/page_list.html"
    context_object_name = "pages"

class AdminPageCreateView(IsAdminMixin, CreateView):
    model = Page
    template_name = "admin/seo_form.html"
    fields = ["title", "slug", "content", "is_published",
              "meta_title", "meta_description", "meta_keywords", "featured_image"]
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
              "meta_title", "meta_description", "meta_keywords", "featured_image"]
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

class AdminMenuDeleteView(IsAdminMixin, DeleteView):
    model = Menu
    success_url = reverse_lazy("management:menu_list")

    def form_valid(self, form):
        messages.success(self.request, "Menu permanently deleted.")
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

class AdminSiteSettingsDeleteView(IsAdminMixin, DeleteView):
    model = SiteSetting
    success_url = reverse_lazy("management:settings_list")

    def form_valid(self, form):
        messages.success(self.request, "Setting permanently deleted.")
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
    template_name = "admin/seo_form.html"
    fields = ["title", "slug", "resource_type", "description", "grade", "learning_area", "file", "is_free", "price", "vendor",
              "meta_title", "meta_description", "meta_keywords", "featured_image"]
    success_url = reverse_lazy("management:resource_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New Resource"
        ctx["cancel_url"] = self.success_url
        ctx["parent_title"] = "Resources"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Resource created successfully.")
        return super().form_valid(form)

class AdminResourceUpdateView(IsAdminMixin, UpdateView):
    model = ResourceItem
    template_name = "admin/seo_form.html"
    fields = ["title", "slug", "resource_type", "description", "grade", "learning_area", "file", "is_free", "price", "vendor",
              "meta_title", "meta_description", "meta_keywords", "featured_image"]
    success_url = reverse_lazy("management:resource_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Resource: {self.object.title}"
        ctx["cancel_url"] = self.success_url
        ctx["parent_title"] = "Resources"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Resource updated successfully.")
        return super().form_valid(form)

class AdminResourceDeleteView(IsAdminMixin, DeleteView):
    model = ResourceItem
    success_url = reverse_lazy("management:resource_list")
    
    def form_valid(self, form):
        messages.success(self.request, "Resource permanently deleted.")
        return super().form_valid(form)


# ── Contact Messages ─────────────────────────────────────────────────────────

class AdminContactMessageListView(IsAdminMixin, ListView):
    model = ContactMessage
    template_name = "admin/contact_message_list.html"
    context_object_name = "contact_messages"
    paginate_by = 20
    ordering = ["-created_at"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["unread_count"] = ContactMessage.objects.filter(is_read=False).count()
        return ctx


class AdminContactMessageDetailView(IsAdminMixin, DetailView):
    model = ContactMessage
    template_name = "admin/contact_message_detail.html"
    context_object_name = "msg"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # auto-mark as read when admin opens it
        obj = self.get_object()
        if not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=["is_read"])
        return response


class AdminContactMessageDeleteView(IsAdminMixin, DeleteView):
    model = ContactMessage
    success_url = reverse_lazy("management:contact_list")

    def form_valid(self, form):
        messages.success(self.request, "Contact message deleted.")
        return super().form_valid(form)


# ── Partners ─────────────────────────────────────────────────────────────────
class AdminPartnerListView(IsAdminMixin, ListView):
    model = Partner
    template_name = "admin/partner_list.html"
    context_object_name = "partners"
    paginate_by = 30
    ordering = ["name"]


class AdminPartnerCreateView(IsAdminMixin, CreateView):
    model = Partner
    template_name = "admin/seo_form.html"
    fields = ["name", "slug", "link", "description", "logo", "show_as_banner", "banner_cta",
              "meta_title", "meta_description", "meta_keywords", "featured_image"]
    success_url = reverse_lazy("management:partner_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Add New Partner"
        ctx["cancel_url"] = self.success_url
        ctx["parent_title"] = "Partners"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"Partner '{form.instance.name}' added successfully.")
        return super().form_valid(form)


class AdminPartnerUpdateView(IsAdminMixin, UpdateView):
    model = Partner
    template_name = "admin/seo_form.html"
    fields = ["name", "slug", "link", "description", "logo", "show_as_banner", "banner_cta",
              "meta_title", "meta_description", "meta_keywords", "featured_image"]
    success_url = reverse_lazy("management:partner_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Partner: {self.object.name}"
        ctx["cancel_url"] = self.success_url
        ctx["parent_title"] = "Partners"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Partner updated successfully.")
        return super().form_valid(form)


class AdminPartnerDeleteView(IsAdminMixin, DeleteView):
    model = Partner
    success_url = reverse_lazy("management:partner_list")

    def form_valid(self, form):
        messages.success(self.request, "Partner deleted.")
        return super().form_valid(form)
