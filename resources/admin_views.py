from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView

from accounts.admin_views import IsAdminMixin
from resources.forms import ResourceItemForm
from resources.models import ResourceItem


class VendorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_content_vendor


# ── Adin Resources CRUD Views ────────────────────────────────────────────────────────────────
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
    form_class = ResourceItemForm
    success_url = reverse_lazy("management:resource_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create New Resource"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Resources"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Resource created successfully.")
        return super().form_valid(form)


class AdminResourceUpdateView(IsAdminMixin, UpdateView):
    model = ResourceItem
    template_name = "admin/seo_form.html"
    form_class = ResourceItemForm
    success_url = reverse_lazy("management:resource_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Resource: {self.object.title}"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Resources"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Resource updated successfully.")
        return super().form_valid(form)


class AdminResourceDeleteView(IsAdminMixin, DeleteView):
    model = ResourceItem
    success_url = reverse_lazy("management:resource_list")

    def form_valid(self, form):
        messages.success(self.request, "Resource permanently deleted.")
        return super().form_valid(form)
