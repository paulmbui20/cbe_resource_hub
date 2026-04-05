"""
resources/views.py

High-performance class-based views for CBE resource browsing.

Key optimisations:
    - select_related() on every FK to eliminate N+1 database queries
    - HTMX-aware pagination: full page for normal requests, partial HTML
      for HTMX requests (infinite scroll / "Load more" pattern)
    - Atomic download counter increment via F() expressions
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models import QuerySet
from django.http import HttpResponse
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import ResourceItemForm

from .models import EducationLevel, Grade, LearningArea, ResourceItem

if TYPE_CHECKING:
    from django.http import HttpRequest


class ResourceListView(ListView):
    """
    Paginated list of ResourceItems with HTMX infinite-scroll support.

    HTMX Usage (in the template):
        <div id="resource-list"
             hx-get="{% url 'resources:list' %}?page={{ page_obj.next_page_number }}"
             hx-trigger="revealed"
             hx-swap="afterend"
             hx-target="#resource-list">
        </div>

    Returns:
        - Full page template ``resources/resource_list.html`` for normal requests
        - Partial template ``resources/partials/resource_cards.html`` for HTMX requests
    """

    model = ResourceItem
    paginate_by = 12
    template_name = "resources/resource_list.html"
    partial_template_name = "resources/partials/resource_cards.html"
    context_object_name = "resources"

    def get_queryset(self) -> QuerySet[ResourceItem]:
        """
        Return an optimised queryset.

        select_related fetches all FK rows in a single JOIN query, completely
        eliminating N+1 database hits when the template accesses
        resource.grade.name, resource.grade.level.name, resource.learning_area.name.
        """
        qs: QuerySet[ResourceItem] = (
            ResourceItem.objects.select_related(
                "grade",
                "grade__level",
                "learning_area",
                "vendor",
            )
            .filter(is_free=True)  # default: show free resources; extend for marketplace
            .order_by("-created_at")
        )

        # --- Optional filtering via GET params ---
        grade_id = self.request.GET.get("grade")
        resource_type = self.request.GET.get("resource_type")
        area_id = self.request.GET.get("area")
        level_id = self.request.GET.get("level")
        q = self.request.GET.get("q", "").strip()

        if grade_id:
            qs = qs.filter(grade_id=grade_id)
        if area_id:
            qs = qs.filter(learning_area_id=area_id)
        if level_id:
            qs = qs.filter(grade__level_id=level_id)
        if q:
            qs = qs.filter(title__icontains=q)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["education_levels"] = EducationLevel.objects.prefetch_related("grades").order_by("order")
        context["learning_areas"] = LearningArea.objects.order_by("name")
        context["current_grade"] = self.request.GET.get("grade", "")
        context["current_area"] = self.request.GET.get("area", "")
        context["current_level"] = self.request.GET.get("level", "")
        context["search_query"] = self.request.GET.get("q", "")
        context["resource_type"] = self.request.GET.get("resource_type", "")
        
        # Pre-fetch user favorites to avoid N+1 queries in the template
        if self.request.user.is_authenticated:
            context["user_favorite_ids"] = set(self.request.user.favorites.values_list("id", flat=True))
        else:
            context["user_favorite_ids"] = set()
            
        return context

    def render_to_response(
        self, context: dict[str, Any], **response_kwargs: Any
    ) -> HttpResponse:
        """
        Return a partial HTML snippet for HTMX requests; full page otherwise.

        This keeps a single view handling both standard navigation and
        HTMX-driven infinite scroll / search without duplication.
        """
        if self.request.headers.get("HX-Request"):
            self.template_name = self.partial_template_name
        return super().render_to_response(context, **response_kwargs)


class ResourceDetailView(DetailView):
    """
    Single resource detail page.

    Atomically increments the download counter on GET so the stat
    reflects page views (for actual file download, wire up a separate
    download endpoint that increments on file serve).
    """

    model = ResourceItem
    template_name = "resources/resource_detail.html"
    context_object_name = "resource"

    def get_queryset(self) -> QuerySet[ResourceItem]:
        return ResourceItem.objects.select_related(
            "grade",
            "grade__level",
            "learning_area",
            "vendor",
        )

    def get_object(self, queryset: QuerySet[ResourceItem] | None = None) -> ResourceItem:
        obj: ResourceItem = super().get_object(queryset)
        obj.increment_downloads()
        return obj


from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string


class ToggleFavoriteView(LoginRequiredMixin, DetailView):
    """
    HTMX endpoint for toggling favorited state of a ResourceItem.
    Returns just the star button partial.
    """
    model = ResourceItem

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        resource = self.get_object()
        user = request.user
        
        # Toggle logic
        if resource in user.favorites.all():
            user.favorites.remove(resource)
            is_favorited = False
        else:
            user.favorites.add(resource)
            is_favorited = True
            
        # If it's an HTMX request, we return just the button snippet.
        if request.headers.get("HX-Request"):
            html = render_to_string(
                "resources/partials/favorite_button.html",
                {"resource": resource, "is_favorited": is_favorited},
                request=request
            )
            return HttpResponse(html)
            
        # Fallback for non-HTMX
        from django.shortcuts import redirect
        return redirect(resource.get_absolute_url())


class VendorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_content_vendor


class ResourceCreateView(VendorRequiredMixin, CreateView):
    model = ResourceItem
    form_class = ResourceItemForm
    template_name = "resources/resource_form.html"

    def form_valid(self, form):
        form.instance.vendor = self.request.user
        messages.success(self.request, "Resource uploaded successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("accounts:dashboard")


class ResourceUpdateView(VendorRequiredMixin, UpdateView):
    model = ResourceItem
    form_class = ResourceItemForm
    template_name = "resources/resource_form.html"

    def get_queryset(self):
        # Only allow editing own resources, unless admin
        qs = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.role == 'admin':
            return qs
        return qs.filter(vendor=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Resource updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("accounts:dashboard")


class ResourceDeleteView(VendorRequiredMixin, DeleteView):
    model = ResourceItem
    template_name = "resources/resource_confirm_delete.html"
    success_url = reverse_lazy("accounts:dashboard")

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.role == 'admin':
            return qs
        return qs.filter(vendor=self.request.user)
        
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Resource deleted successfully.")
        return super().delete(request, *args, **kwargs)
