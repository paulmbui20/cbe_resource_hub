from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView

from accounts.admin_views import IsAdminMixin
from resources.forms import ResourceItemForm
from resources.models import ResourceItem
from website.forms.admin_comment import AdminResourceCommentForm
from resources.models import ResourceComment


class VendorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated and self.request.user.is_content_vendor
        )


# ── Adin Resources CRUD Views ────────────────────────────────────────────────────────────────
class AdminResourceListView(IsAdminMixin, ListView):
    model = ResourceItem
    template_name = "admin/resource_list.html"
    context_object_name = "resources"
    paginate_by = 30

    def get_queryset(self):
        qs = ResourceItem.objects.select_related(
            "vendor", "grade", "learning_area"
        ).order_by("-created_at")
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


# ── Resource Comments ─────────────────────────────────────────────────────────
class AdminResourceCommentListView(IsAdminMixin, ListView):
    model = ResourceComment
    template_name = "admin/resource_comment_list.html"
    context_object_name = "comments"
    paginate_by = 25

    def get_queryset(self):
        qs = ResourceComment.objects.select_related(
            "resource", "user", "parent"
        ).order_by("-created_at")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(body__icontains=q) | Q(name__icontains=q) | Q(email__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class AdminResourceCommentUpdateView(IsAdminMixin, UpdateView):
    model = ResourceComment
    form_class = AdminResourceCommentForm
    template_name = "admin/generic_form.html"
    success_url = reverse_lazy("management:resource_comment_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Comment by {self.object.name}"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Resource Comments"
        # Link to the resource details page if available
        if self.object.resource:
            context["detail_url"] = self.object.resource.get_absolute_url()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Comment updated successfully.")
        return super().form_valid(form)


class AdminResourceCommentDeleteView(IsAdminMixin, DeleteView):
    model = ResourceComment
    success_url = reverse_lazy("management:resource_comment_list")

    def form_valid(self, form):
        messages.success(self.request, "Comment deleted.")
        return super().form_valid(form)
