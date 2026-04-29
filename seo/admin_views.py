from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from cms.models import Page
from resources.models import ResourceItem
from seo.forms import SlugRedirectForm
from seo.models import SlugRedirect
from website.admin_views import IsAdminMixin


# ── SlugRedirect Views ───────────────────────────────────────────────────────
class AdminSlugRedirectListView(IsAdminMixin, ListView):
    template_name = 'admin/seo/redirect_list.html'
    context_object_name = 'redirects'
    paginate_by = 30

    def get_queryset(self):
        qs = SlugRedirect.objects.select_related('content_type').order_by('-created_at')
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(old_slug__icontains=q) | qs.filter(new_slug__icontains=q)
            qs = qs.filter(old_slug__icontains=q) | SlugRedirect.objects.filter(new_slug__icontains=q).select_related(
                'content_type')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['total_hits'] = sum(SlugRedirect.objects.values_list('hit_count', flat=True))
        return context


class AdminSlugRedirectCreateView(IsAdminMixin, CreateView):
    model = SlugRedirect
    form_class = SlugRedirectForm
    template_name = 'admin/seo/redirect_form.html'
    success_url = reverse_lazy('management:seo_redirect_list')

    def form_valid(self, form):
        messages.success(self.request,
                         f"Redirect from  /{form.instance.old_slug}/  →  /{form.instance.new_slug}/  created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Slug Redirect'
        context['action_label'] = 'Create Redirect'
        return context


class AdminSlugRedirectUpdateView(IsAdminMixin, UpdateView):
    model = SlugRedirect
    form_class = SlugRedirectForm
    template_name = 'admin/seo/redirect_form.html'
    success_url = reverse_lazy('management:seo_redirect_list')

    def form_valid(self, form):
        messages.success(self.request, "Redirect updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Slug Redirect'
        context['action_label'] = 'Save Changes'
        return context


class AdminSlugRedirectDeleteView(IsAdminMixin, DeleteView):
    model = SlugRedirect
    success_url = reverse_lazy('management:seo_redirect_list')

    def form_valid(self, form):
        messages.success(self.request, "Redirect deleted successfully.")
        return super().form_valid(form)


class AdminPagesSEOAuditView(IsAdminMixin, ListView):
    template_name = 'admin/seo/pages_seo_audit.html'
    paginate_by = 12
    context_object_name = "pages"

    def get_queryset(self):
        qs = Page.objects.only(
            'title', 'slug', 'meta_title', 'meta_description',
            'meta_keywords', 'is_published', 'meta_keywords'
        ).filter(
            Q(meta_title__isnull=True) | Q(meta_title='') |
            Q(meta_description__isnull=True) | Q(meta_description='') |
            Q(meta_keywords__isnull=True) | Q(meta_keywords='')
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


# ── SEO Audit View ───────────────────────────────────────────────────────────
class AdminResourcesSEOAuditView(IsAdminMixin, ListView):
    template_name = 'admin/seo/resources_seo_audit.html'
    paginate_by = 12
    context_object_name = "resources"

    def get_queryset(self):
        resources = ResourceItem.objects.filter(
            Q(meta_description__isnull=True) | Q(meta_description='') |
            Q(meta_title__isnull=True) | Q(meta_title='') |
            Q(meta_keywords__isnull=True) | Q(meta_keywords='')
        )

        return resources
