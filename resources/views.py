"""
resources/views.py

High-performance class-based views for CBE resource browsing.

Key optimizations:
    - select_related() on every FK to eliminate N+1 database queries
    - HTMX-aware pagination: full page for normal requests, partial HTML
      for HTMX requests (infinite scroll / "Load more" pattern)
    - Atomic download counter increment via F() expressions
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet, Q
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView

from core.models import AcademicSession
from .admin_views import VendorRequiredMixin
from .cache import get_learning_areas, get_grades, get_resource_types, get_education_levels, \
    get_slug_based_object_or_404_with_cache, get_academic_sessions
from .forms import ResourceItemForm
from .models import EducationLevel, LearningArea, ResourceItem, Grade


class ResourceListView(ListView):
    """
    Paginated list of ResourceItems with HTMX infinite-scroll support.
    Returns:
        - Full page template ``resources/resource_list.html`` for normal requests
        - Partial template ``resources/partials/resource_cards.html`` for HTMX requests
    """

    paginate_by = 24
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
            ResourceItem.objects.filter(is_free=True)  # default: show free resources; extend for marketplace
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
            qs = qs.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        if resource_type:
            qs = qs.filter(resource_type=resource_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["education_levels"] = get_education_levels()
        context["grades"] = get_grades()
        context["learning_areas"] = get_learning_areas()
        context["resource_types"] = get_resource_types()
        context["current_grade"] = self.request.GET.get("grade", "")
        context["current_area"] = self.request.GET.get("area", "")
        context["current_level"] = self.request.GET.get("level", "")
        context["search_query"] = self.request.GET.get("q", "")
        context["current_resource_type"] = self.request.GET.get("resource_type", "")
        context["current_grade"] = self.request.GET.get("grade", "")

        # Pre-fetch user favorites to avoid N+1 queries in the template
        if self.request.user.is_authenticated:
            context["user_favorite_ids"] = set(self.request.user.favorites.values_list("id", flat=True))
        else:
            context["user_favorite_ids"] = set()

        return context

    def render_to_response(self, context, **response_kwargs):
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
    """
    model = ResourceItem
    template_name = "resources/resource_detail.html"
    context_object_name = "resource"

    def get_queryset(self):
        # The custom manager already applies select_related; return it directly.
        return ResourceItem.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Single indexed EXISTS query rather than evaluating full M2M QS
        if self.request.user.is_authenticated:
            context["user_favorite_ids"] = set(
                self.request.user.favorites.values_list("id", flat=True)
            )
        else:
            context["user_favorite_ids"] = set()
        return context


@require_POST
def increment_downloads(request, slug):
    try:
        resource_item = ResourceItem.objects.get(slug=slug)
        resource_item_initial_downloads = resource_item.downloads
        resource_item.increment_downloads()
        resource_item_final_downloads = resource_item.downloads
        message = f"Download incremented from {resource_item_initial_downloads} to {resource_item_final_downloads}"
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

    def post(self, request, *args, **kwargs):
        resource = self.get_object()
        user = request.user

        # Use EXISTS query instead of evaluating the full M2M QS.
        is_favorited = user.favorites.filter(pk=resource.pk).exists()
        if is_favorited:
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
    template_name = "resources/resource_type_detail.html"
    partial_template_name = "resources/partials/resource_cards.html"
    context_object_name = "resources"
    paginate_by = 24

    def get_queryset(self) -> QuerySet[ResourceItem]:
        self.resource_type = self.kwargs["resource_type"]

        qs: QuerySet[ResourceItem] = (
            ResourceItem.objects
            .filter(resource_type=self.resource_type, is_free=True)
        )

        q = self.request.GET.get("q")
        q = q.strip() if q else ''

        learning_area_id = self.request.GET.get("learning_area")
        learning_area_id = int(learning_area_id) if learning_area_id else None
        grade_id = self.request.GET.get("grade")
        grade_id = int(grade_id) if grade_id else None
        education_level_id = self.request.GET.get("education_level")
        education_level_id = int(education_level_id) if education_level_id else None

        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        if learning_area_id:
            qs = qs.filter(learning_area_id=learning_area_id)
        if grade_id:
            qs = qs.filter(grade_id=grade_id)

        if education_level_id:
            qs = qs.filter(grade__level__id=education_level_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        info = RESOURCE_TYPE_INFO.get(self.resource_type,
                                      {"icon": "📂", "label": self.resource_type.replace("_", " ").title(), "desc": ""})
        context["resource_type_key"] = self.resource_type
        context["resource_type_label"] = info["label"]
        context["resource_type_icon"] = info["icon"]
        context["resource_type_desc"] = info["desc"]
        # For related types sidebar / cross-links
        context["all_resource_types"] = RESOURCE_TYPE_INFO
        context['current_learning_area'] = self.request.GET.get("learning_area", '')
        context['current_education_level'] = self.request.GET.get("education_level", '')
        context['current_grade'] = self.request.GET.get("grade", '')
        context['search_query'] = self.request.GET.get("q", '')
        context["education_levels"] = get_education_levels()
        context["grades"] = get_grades()
        context["learning_areas"] = get_learning_areas()
        context["resource_types"] = get_resource_types()

        # Pre-fetch user favorites to avoid N+1 queries in the template
        if self.request.user.is_authenticated:
            context["user_favorite_ids"] = set(self.request.user.favorites.values_list("id", flat=True))
        else:
            context["user_favorite_ids"] = set()

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial HTML snippet for HTMX requests; full page otherwise.
        """
        if self.request.headers.get("HX-Request"):
            self.template_name = self.partial_template_name
        return super().render_to_response(context, **response_kwargs)


class EducationLevelDetailsView(ListView):
    """
    SEO-optimized landing page for a specific Education Level.

    URL: /resources/education-levels/<education_level>/

    """
    template_name = "resources/education_level_details.html"
    partial_template_name = "resources/partials/resource_cards.html"
    context_object_name = "resources"
    paginate_by = 24

    def get_queryset(self) -> QuerySet[ResourceItem]:
        self.education_level = self.kwargs["slug"]
        qs: QuerySet[ResourceItem] = (
            ResourceItem.objects.filter(grade__level__slug=self.education_level)
        )

        q = self.request.GET.get("q")
        q = q.strip() if q else ''

        learning_area_id = self.request.GET.get("learning_area")
        learning_area_id = int(learning_area_id) if learning_area_id else None
        grade_id = self.request.GET.get("grade")
        grade_id = int(grade_id) if grade_id else None
        education_level_id = self.request.GET.get("education_level")
        education_level_id = int(education_level_id) if education_level_id else None
        resource_type = self.request.GET.get("resource_type")
        resource_type = str(resource_type) if resource_type else None

        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        if learning_area_id:
            qs = qs.filter(learning_area_id=learning_area_id)
        if grade_id:
            qs = qs.filter(grade_id=grade_id)

        if education_level_id:
            qs = qs.filter(grade__level__id=education_level_id)

        if resource_type:
            qs = qs.filter(resource_type=resource_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["education_level"] = get_slug_based_object_or_404_with_cache(EducationLevel, self.education_level)
        context["all_education_levels"] = get_education_levels()
        context["grades"] = get_grades()
        context["learning_areas"] = get_learning_areas()
        context["resource_types"] = get_resource_types()

        context['current_learning_area'] = self.request.GET.get("learning_area", '')
        context['current_resource_type'] = self.request.GET.get("resource_type", '')
        context['current_grade'] = self.request.GET.get("grade", '')
        context['search_query'] = self.request.GET.get("q", '')

        # Pre-fetch user favorites to avoid N+1 queries in the template
        if self.request.user.is_authenticated:
            context["user_favorite_ids"] = set(self.request.user.favorites.values_list("id", flat=True))
        else:
            context["user_favorite_ids"] = set()

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial HTML snippet for HTMX requests; full page otherwise.
        """
        if self.request.headers.get("HX-Request"):
            self.template_name = self.partial_template_name
        return super().render_to_response(context, **response_kwargs)


class LearningAreaDetailsView(ListView):
    """
    SEO-optimized landing page for a specific Learning Area.
    URL: /resources/learning-areas/<learning_area>/
    """
    template_name = "resources/learning_area_details.html"
    partial_template_name = "resources/partials/resource_cards.html"
    context_object_name = "resources"
    paginate_by = 24

    def get_queryset(self) -> QuerySet[ResourceItem]:
        self.learning_area = self.kwargs["slug"]
        qs = (
            ResourceItem.objects.filter(learning_area__slug=self.learning_area)
        )

        q = self.request.GET.get("q")
        q = q.strip() if q else ''
        resource_type = self.request.GET.get("resource_type")
        resource_type = str(resource_type) if resource_type else None
        education_level_id = self.request.GET.get("education_level")
        education_level_id = int(education_level_id) if education_level_id else None

        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if education_level_id:
            qs = qs.filter(grade__level_id=education_level_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["learning_area"] = get_slug_based_object_or_404_with_cache(LearningArea, self.learning_area)

        context["education_levels"] = get_education_levels()
        context["grades"] = get_grades()
        context["learning_areas"] = get_learning_areas()
        context["resource_types"] = get_resource_types()

        context['current_education_level'] = self.request.GET.get("education_level", '')
        context['current_resource_type'] = self.request.GET.get("resource_type", '')
        context['current_grade'] = self.request.GET.get("grade", '')
        context['search_query'] = self.request.GET.get("q", '')

        # Pre-fetch user favorites to avoid N+1 queries in the template
        if self.request.user.is_authenticated:
            context["user_favorite_ids"] = set(self.request.user.favorites.values_list("id", flat=True))
        else:
            context["user_favorite_ids"] = set()

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial HTML snippet for HTMX requests; full page otherwise.
        """
        if self.request.headers.get("HX-Request"):
            self.template_name = self.partial_template_name
        return super().render_to_response(context, **response_kwargs)


class GradeDetailsView(ListView):
    """
    SEO-optimized landing page for a specific Grade.
    URL: /resources/grades/<grade>/
    """
    template_name = "resources/grade_details.html"
    partial_template_name = "resources/partials/resource_cards.html"
    context_object_name = "resources"
    paginate_by = 24

    def get_queryset(self) -> QuerySet[ResourceItem]:
        self.grade = self.kwargs["slug"]
        qs = (
            ResourceItem.objects.filter(grade__slug=self.grade)
        )

        q = self.request.GET.get("q")
        q = q.strip() if q else ''

        learning_area_id = self.request.GET.get("learning_area")
        learning_area_id = int(learning_area_id) if learning_area_id else None
        resource_type = self.request.GET.get("resource_type")
        resource_type = str(resource_type) if resource_type else None

        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        if learning_area_id:
            qs = qs.filter(learning_area_id=learning_area_id)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grade"] = get_slug_based_object_or_404_with_cache(Grade, self.grade)
        context["all_grades"] = get_grades()
        context["learning_areas"] = get_learning_areas()
        context["resource_types"] = get_resource_types()

        context['current_learning_area'] = self.request.GET.get("learning_area", '')
        context['current_resource_type'] = self.request.GET.get("resource_type", '')
        context['search_query'] = self.request.GET.get("q", '')

        # Pre-fetch user favorites to avoid N+1 queries in the template
        if self.request.user.is_authenticated:
            context["user_favorite_ids"] = set(self.request.user.favorites.values_list("id", flat=True))
        else:
            context["user_favorite_ids"] = set()

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial HTML snippet for HTMX requests; full page otherwise.
        """
        if self.request.headers.get("HX-Request"):
            self.template_name = self.partial_template_name
        return super().render_to_response(context, **response_kwargs)


class AcademicSessionDetailView(ListView):
    template_name = "resources/academic_session_detail.html"
    partial_template_name = "resources/partials/resource_cards.html"
    context_object_name = "resources"
    paginate_by = 24

    def get_queryset(self) -> QuerySet[ResourceItem]:
        self.academic_session = self.kwargs["slug"]
        qs = (
            ResourceItem.objects.filter(academic_session__slug=self.academic_session)
        )

        q = self.request.GET.get("q")
        q = q.strip() if q else ''

        learning_area_id = self.request.GET.get("learning_area")
        learning_area_id = int(learning_area_id) if learning_area_id else None
        resource_type = self.request.GET.get("resource_type")
        resource_type = str(resource_type) if resource_type else None
        grade = self.request.GET.get("grade", '')
        grade = int(grade) if grade else None

        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        if learning_area_id:
            qs = qs.filter(learning_area_id=learning_area_id)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if grade:
            qs = qs.filter(grade_id=grade)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["academic_session"] = get_slug_based_object_or_404_with_cache(AcademicSession, self.academic_session)
        context["all_academic_sessions"] = get_academic_sessions()
        context["grades"] = get_grades()
        context["learning_areas"] = get_learning_areas()
        context["resource_types"] = get_resource_types()

        context['current_learning_area'] = self.request.GET.get("learning_area", '')
        context['current_resource_type'] = self.request.GET.get("resource_type", '')
        context['current_grade'] = self.request.GET.get("grade", '')
        context['search_query'] = self.request.GET.get("q", '')

        # Pre-fetch user favorites to avoid N+1 queries in the template
        if self.request.user.is_authenticated:
            context["user_favorite_ids"] = set(self.request.user.favorites.values_list("id", flat=True))
        else:
            context["user_favorite_ids"] = set()

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial HTML snippet for HTMX requests; full page otherwise.
        """
        if self.request.headers.get("HX-Request"):
            self.template_name = self.partial_template_name
        return super().render_to_response(context, **response_kwargs)


class LearningAreaListView(ListView):
    """
    SEO-optimized landing page for all Learning Areas.
    URL: `/resources/learning-areas/`
    Paginated list of the Learning Areas with infinite scrolling.
    Returns:
        - Full page template ``resources/learning_areas_list.html`` for normal requests
        - Partial template ``resources/partials/filter_cards.html`` for HTMX requests
    """

    paginate_by = 24
    template_name = "resources/learning_areas_list.html"
    partial_template_name = "resources/partials/filter_cards.html"
    context_object_name = "filters"

    def get_queryset(self) -> list[LearningArea]:
        """
        Return all Learning Areas with infinite scrolling.
        """

        qs = get_learning_areas()

        q = self.request.GET.get("q")
        q = q.strip() if q else None

        if q:
            qs = [x for x in qs if q.lower() in x.name.lower()]

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q")

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial HTML snippet for HTMX requests; full page otherwise.
        """

        if self.request.headers.get("HX-Request"):
            self.template_name = self.partial_template_name

        return super().render_to_response(context, **response_kwargs)


class GradeListView(ListView):
    """
    SEO-optimized landing page for all Grades.
    URL: `/resources/grades/`
    Paginated list of the Grades with infinite scrolling.
    Returns:
        - Full page template ``resources/grade_list.html`` for normal requests
        - Partial template ``resources/partials/filter_cards.html`` for HTMX requests
    """

    paginate_by = 24
    template_name = "resources/grade_list.html"
    partial_template_name = "resources/partials/filter_cards.html"
    context_object_name = "filters"

    def get_queryset(self) -> list[Grade]:
        """
        Return all Grades with infinite scrolling.
        """

        qs = get_grades()

        q = self.request.GET.get("q")
        q = q.strip() if q else None

        if q:
            qs = [x for x in qs if q.lower() in x.name.lower()]

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q")

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial HTML snippet for HTMX requests; full page otherwise.
        """

        if self.request.headers.get("HX-Request"):
            self.template_name = self.partial_template_name
        return super().render_to_response(context, **response_kwargs)


class AcademicSessionListView(ListView):
    paginate_by = 24
    template_name = "resources/academic_session_list.html"
    partial_template_name = "resources/partials/academic_sessions_cards.html"
    context_object_name = "academic_sessions"

    def get_queryset(self):
        qs = get_academic_sessions()

        q = self.request.GET.get("q")
        q = q.strip() if q else None

        if q:
            q_lower = q.lower()
            qs = [
                s for s in qs 
                if q_lower in str(s.current_year.year).lower() 
                or q_lower in str(s.current_term.term_number).lower()
            ]
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q")

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial HTML snippet for HTMX requests; full page otherwise.
        """

        if self.request.headers.get("HX-Request"):
            self.template_name = self.partial_template_name
        return super().render_to_response(context, **response_kwargs)


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
