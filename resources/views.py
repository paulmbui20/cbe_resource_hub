"""
resources/views.py

High-performance class-based views for CBE resource browsing.

Key optimizations:
    - select_related() on every FK to eliminate N+1 database queries
    - HTMX-aware pagination: full page for normal requests, partial HTML
      for HTMX requests (infinite scroll / "Load more" pattern)
    - Atomic download counter increment via F() expressions
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models import QuerySet
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.contrib import messages

from .admin_views import VendorRequiredMixin
from .forms import ResourceItemForm

from .models import EducationLevel, LearningArea, ResourceItem

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
        resource_type = str(resource_type) if resource_type else None
        area_id = self.request.GET.get("area")
        level_id = self.request.GET.get("level")
        q = self.request.GET.get("q")
        q = q.strip() if q else None

        if grade_id:
            qs = qs.filter(grade_id=grade_id)
        if area_id:
            qs = qs.filter(learning_area_id=area_id)
        if level_id:
            qs = qs.filter(grade__level_id=level_id)
        if q:
            from django.db.models import Q as DQ
            qs = qs.filter(
                DQ(title__icontains=q) | DQ(description__icontains=q)
            )
        if resource_type:
            qs = qs.filter(resource_type=resource_type)

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["education_levels"] = EducationLevel.objects.prefetch_related("grades").order_by("order")
        context["learning_areas"] = LearningArea.objects.order_by("name")
        context["resource_types"] = dict(ResourceItem._meta.get_field("resource_type").choices)
        context["current_grade"] = self.request.GET.get("grade", "")
        context["current_area"] = self.request.GET.get("area", "")
        context["current_level"] = self.request.GET.get("level", "")
        context["search_query"] = self.request.GET.get("q", "")
        context["current_resource_type"] = self.request.GET.get("resource_type", "")

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

        Also returns a compact suggestions dropdown partial when the request
        includes ``suggestions=1`` (used by the homepage live-search bar).
        """
        if self.request.GET.get("suggestions") == "1":
            self.template_name = "resources/partials/search_suggestions.html"
        elif self.request.headers.get("HX-Request"):
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
        return obj


@require_POST
def increment_downloads(request, slug):
    try:
        resource_item = ResourceItem.objects.get(slug=slug)
        resource_item_initial_downloads = resource_item.downloads
        resource_item.increment_downloads()
        resource_item_final_downloads = resource_item.downloads
        message = f"Download incremented from {resource_item_initial_downloads} to {resource_item_final_downloads}"
        print(message)
        return JsonResponse(
            {
                "success": message
            },
            status=200
        )

    except ResourceItem.DoesNotExist:
        return JsonResponse({"error": "Resource item not found"}, status=404)


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


# ── Resource Type Detail (SEO landing page per type) ──────────────────────────
# Map resource_type key → (icon emoji, short description for the landing page)
RESOURCE_TYPE_INFO: dict[str, dict] = {
    "lesson_plan": {"icon": "📋", "label": "Lesson Plans",
                    "desc": "Day-by-day structured teaching blueprints for effective classroom delivery."},
    "schemes_of_work": {"icon": "📅", "label": "Schemes of Work",
                        "desc": "Term-long curriculum plans helping teachers cover the full syllabus on time."},
    "curriculum_design": {"icon": "🗺️", "label": "Curriculum Design",
                          "desc": "Comprehensive curriculum frameworks and competency-based programme designs."},
    "record_of_work": {"icon": "📒", "label": "Records of Work",
                       "desc": "Official records documenting what has been taught in each class and term."},
    "teachers_guide": {"icon": "📖", "label": "Teachers' Guides",
                       "desc": "Step-by-step instructional manuals to help educators deliver quality lessons."},
    "textbook": {"icon": "📚", "label": "Textbooks",
                 "desc": "Approved learner study books aligned to the latest CBC/CBE curriculum."},
    "notes": {"icon": "📝", "label": "Notes",
              "desc": "Concise revision notes and summaries covering key topics in every learning area."},
    "exam": {"icon": "✏️", "label": "Exams & Past Papers",
             "desc": "Past examination papers and mock exams to help learners prepare and practice."},
    "report_card": {"icon": "🗒️", "label": "Report Cards",
                    "desc": "Official learner assessment and progress report card templates."},
    "other": {"icon": "📂", "label": "Other Resources",
              "desc": "Additional CBC-aligned resources that don't fit a specific category above."},
    "holiday_assignment": {"icon": "📝", "label": "Holiday Assignment",
              "desc": "Helpful holiday assignments to keep learner engaged even over the holidays"},
    "setbook_guide": {"icon": "📝", "label": "Set Book Guide",
              "desc": "Set Book Guide"},
}


class ResourceTypeDetailView(ListView):
    """
    SEO-optimized landing page for a specific resource type.

    URL: /resources/type/<resource_type>/
    """

    model = ResourceItem
    template_name = "resources/resource_type_detail.html"
    context_object_name = "resources"
    paginate_by = 12

    def get_queryset(self) -> QuerySet[ResourceItem]:
        self.resource_type = self.kwargs["resource_type"]
        return (
            ResourceItem.objects.select_related("grade", "grade__level", "learning_area")
            .filter(resource_type=self.resource_type, is_free=True)
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        info = RESOURCE_TYPE_INFO.get(self.resource_type,
                                      {"icon": "📂", "label": self.resource_type.replace("_", " ").title(), "desc": ""})
        ctx["resource_type_key"] = self.resource_type
        ctx["resource_type_label"] = info["label"]
        ctx["resource_type_icon"] = info["icon"]
        ctx["resource_type_desc"] = info["desc"]
        ctx["resource_type_count"] = self.get_queryset().count()
        # For related types sidebar / cross-links
        ctx["all_resource_types"] = RESOURCE_TYPE_INFO
        return ctx


# user/vendor resource crud views

class ResourceCreateView(VendorRequiredMixin, CreateView):
    model = ResourceItem
    form_class = ResourceItemForm
    template_name = "resources/resource_form.html"

    def form_valid(self, form):
        form.instance.vendor = self.request.user
        form.instance.is_free = True
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
        form.instance.is_free = True
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
