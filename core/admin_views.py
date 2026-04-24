from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from accounts.admin_views import IsAdminMixin
from core.models import Year, Term, AcademicSession


class AdminYearListView(IsAdminMixin, ListView):
    context_object_name = "years"
    template_name = "admin/core/year_list.html"
    model = Year
    paginate_by = 15


class AdminYearCreateView(IsAdminMixin, CreateView):
    model = Year
    template_name = "admin/generic_form.html"
    fields = ["year", ]
    success_url = reverse_lazy("management:year_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create New Year"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Years"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Year created successfully.")
        return super().form_valid(form)


class AdminYearUpdateView(IsAdminMixin, UpdateView):
    model = Year
    template_name = "admin/generic_form.html"
    fields = ["year", ]
    success_url = reverse_lazy("management:year_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Year"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Years"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Year updated successfully.")
        return super().form_valid(form)


class AdminYearDeleteView(IsAdminMixin, DeleteView):
    model = Year
    success_url = reverse_lazy("management:year_list")

    def form_valid(self, form):
        messages.success(self.request, "Year deleted successfully.")
        return super().form_valid(form)


class AdminTermListView(IsAdminMixin, ListView):
    context_object_name = "terms"
    model = Term
    template_name = "admin/core/term_list.html"
    paginate_by = 15


class AdminTermCreateView(IsAdminMixin, CreateView):
    model = Term
    template_name = "admin/generic_form.html"
    success_url = reverse_lazy("management:term_list")
    fields = ["term_number", ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create New Term"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Terms"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Term created successfully.")
        return super().form_valid(form)


class AdminTermUpdateView(IsAdminMixin, UpdateView):
    model = Term
    template_name = "admin/generic_form.html"
    success_url = reverse_lazy("management:term_list")
    fields = ["term_number", ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Term"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Terms"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Term updated successfully.")
        return super().form_valid(form)


class AdminTermDeleteView(IsAdminMixin, DeleteView):
    model = Term
    success_url = reverse_lazy("management:term_list")

    def form_valid(self, form):
        messages.success(self.request, "Term deleted successfully.")
        return super().form_valid(form)


class AdminAcademicSessionListView(IsAdminMixin, ListView):
    context_object_name = "academic_sessions"
    model = AcademicSession
    template_name = "admin/core/academic_session_list.html"
    paginate_by = 24


class AdminAcademicSessionCreateView(IsAdminMixin, CreateView):
    model = AcademicSession
    fields = ["current_year", "current_term", ]
    template_name = "admin/generic_form.html"
    success_url = reverse_lazy("management:academic_session_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create New Academic Session"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Academic Sessions"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Academic session created successfully.")
        return super().form_valid(form)


class AdminAcademicSessionUpdateView(IsAdminMixin, UpdateView):
    model = AcademicSession
    template_name = "admin/generic_form.html"
    fields = ["current_year", "current_term", ]
    success_url = reverse_lazy("management:academic_session_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Academic Session"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Academic Sessions"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Academic session updated successfully.")
        return super().form_valid(form)


class AdminAcademicSessionDeleteView(IsAdminMixin, DeleteView):
    model = AcademicSession
    success_url = reverse_lazy("management:academic_session_list")

    def form_valid(self, form):
        messages.success(self.request, "Academic session deleted successfully.")
        return super().form_valid(form)
