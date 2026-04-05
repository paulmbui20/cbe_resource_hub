from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from website.admin_views import IsAdminMixin
from resources.models import EducationLevel, Grade, LearningArea
from cms.models import MenuItem

# ── Education Levels ────────────────────────────────────────────────────────
class AdminEducationLevelListView(IsAdminMixin, ListView):
    model = EducationLevel
    template_name = "admin/basic_list.html"
    context_object_name = "items"
    extra_context = {
        "title": "Education Levels",
        "add_url": "management:level_add",
        "edit_url": "management:level_edit",
        "delete_url": "management:level_delete",
        "columns": [("Name", "name"), ("Slug", "slug"), ("Order", "order")]
    }

class AdminEducationLevelCreateView(IsAdminMixin, CreateView):
    model = EducationLevel
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:level_list")
    extra_context = {"title": "Add Education Level"}

    def form_valid(self, form):
        messages.success(self.request, "Education Level created.")
        return super().form_valid(form)

class AdminEducationLevelUpdateView(IsAdminMixin, UpdateView):
    model = EducationLevel
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:level_list")
    extra_context = {"title": "Edit Education Level"}

    def form_valid(self, form):
        messages.success(self.request, "Education Level updated.")
        return super().form_valid(form)

class AdminEducationLevelDeleteView(IsAdminMixin, DeleteView):
    model = EducationLevel
    success_url = reverse_lazy("management:level_list")
    def form_valid(self, form):
        messages.success(self.request, "Deleted Education Level.")
        return super().form_valid(form)

# ── Grades ──────────────────────────────────────────────────────────────────
class AdminGradeListView(IsAdminMixin, ListView):
    model = Grade
    template_name = "admin/basic_list.html"
    context_object_name = "items"
    extra_context = {
        "title": "Grades",
        "add_url": "management:grade_add",
        "edit_url": "management:grade_edit",
        "delete_url": "management:grade_delete",
        "columns": [("Name", "name"), ("Level", "level"), ("Order", "order")]
    }

class AdminGradeCreateView(IsAdminMixin, CreateView):
    model = Grade
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:grade_list")
    extra_context = {"title": "Add Grade"}

    def form_valid(self, form):
        messages.success(self.request, "Grade created.")
        return super().form_valid(form)

class AdminGradeUpdateView(IsAdminMixin, UpdateView):
    model = Grade
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:grade_list")
    extra_context = {"title": "Edit Grade"}

    def form_valid(self, form):
        messages.success(self.request, "Grade updated.")
        return super().form_valid(form)

class AdminGradeDeleteView(IsAdminMixin, DeleteView):
    model = Grade
    success_url = reverse_lazy("management:grade_list")
    def form_valid(self, form):
        messages.success(self.request, "Deleted Grade.")
        return super().form_valid(form)

# ── Learning Areas ──────────────────────────────────────────────────────────
class AdminLearningAreaListView(IsAdminMixin, ListView):
    model = LearningArea
    template_name = "admin/basic_list.html"
    context_object_name = "items"
    extra_context = {
        "title": "Learning Areas",
        "add_url": "management:learningarea_add",
        "edit_url": "management:learningarea_edit",
        "delete_url": "management:learningarea_delete",
        "columns": [("Name", "name"), ("Slug", "slug")]
    }

class AdminLearningAreaCreateView(IsAdminMixin, CreateView):
    model = LearningArea
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:learningarea_list")
    extra_context = {"title": "Add Learning Area"}

    def form_valid(self, form):
        messages.success(self.request, "Learning Area created.")
        return super().form_valid(form)

class AdminLearningAreaUpdateView(IsAdminMixin, UpdateView):
    model = LearningArea
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:learningarea_list")
    extra_context = {"title": "Edit Learning Area"}

    def form_valid(self, form):
        messages.success(self.request, "Learning Area updated.")
        return super().form_valid(form)

class AdminLearningAreaDeleteView(IsAdminMixin, DeleteView):
    model = LearningArea
    success_url = reverse_lazy("management:learningarea_list")
    def form_valid(self, form):
        messages.success(self.request, "Deleted Learning Area.")
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
    fields = "__all__"
    success_url = reverse_lazy("management:menuitem_list")
    extra_context = {"title": "Add Menu Item"}

    def form_valid(self, form):
        messages.success(self.request, "Menu Item created.")
        return super().form_valid(form)

class AdminMenuItemUpdateView(IsAdminMixin, UpdateView):
    model = MenuItem
    template_name = "admin/generic_form.html"
    fields = "__all__"
    success_url = reverse_lazy("management:menuitem_list")
    extra_context = {"title": "Edit Menu Item"}

    def form_valid(self, form):
        messages.success(self.request, "Menu Item updated.")
        return super().form_valid(form)

class AdminMenuItemDeleteView(IsAdminMixin, DeleteView):
    model = MenuItem
    success_url = reverse_lazy("management:menuitem_list")
    def form_valid(self, form):
        messages.success(self.request, "Deleted Menu Item.")
        return super().form_valid(form)
