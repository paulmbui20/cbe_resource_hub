from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django import forms
from django.contrib import messages

from seo.models import SlugRedirect
from website.admin_views import IsAdminMixin


# ── SlugRedirect Form ────────────────────────────────────────────────────────
class SlugRedirectForm(forms.ModelForm):
    class Meta:
        model = SlugRedirect
        fields = ['old_slug', 'new_slug']
        widgets = {
            'old_slug': forms.TextInput(attrs={
                'class': 'w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary transition-all',
                'placeholder': 'e.g. old-page-name',
            }),
            'new_slug': forms.TextInput(attrs={
                'class': 'w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary transition-all',
                'placeholder': 'e.g. new-page-name',
            }),
        }
        help_texts = {
            'old_slug': 'The old URL slug that should be redirected (e.g. my-old-post)',
            'new_slug': 'The new URL slug to redirect traffic to (e.g. my-new-post)',
        }


# ── SlugRedirect Views ───────────────────────────────────────────────────────
class AdminSlugRedirectListView(IsAdminMixin, ListView):
    model = SlugRedirect
    template_name = 'admin/seo/redirect_list.html'
    context_object_name = 'redirects'
    paginate_by = 30

    def get_queryset(self):
        qs = SlugRedirect.objects.select_related('content_type').order_by('-created_at')
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(old_slug__icontains=q) | qs.filter(new_slug__icontains=q)
            qs = qs.filter(old_slug__icontains=q) | SlugRedirect.objects.filter(new_slug__icontains=q).select_related('content_type')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['total_redirects'] = SlugRedirect.objects.count()
        ctx['total_hits'] = sum(SlugRedirect.objects.values_list('hit_count', flat=True))
        return ctx


class AdminSlugRedirectCreateView(IsAdminMixin, CreateView):
    model = SlugRedirect
    form_class = SlugRedirectForm
    template_name = 'admin/seo/redirect_form.html'
    success_url = reverse_lazy('management:seo_redirect_list')

    def form_valid(self, form):
        messages.success(self.request, f"Redirect from  /{form.instance.old_slug}/  →  /{form.instance.new_slug}/  created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Create Slug Redirect'
        ctx['action_label'] = 'Create Redirect'
        return ctx


class AdminSlugRedirectUpdateView(IsAdminMixin, UpdateView):
    model = SlugRedirect
    form_class = SlugRedirectForm
    template_name = 'admin/seo/redirect_form.html'
    success_url = reverse_lazy('management:seo_redirect_list')

    def form_valid(self, form):
        messages.success(self.request, "Redirect updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Edit Slug Redirect'
        ctx['action_label'] = 'Save Changes'
        return ctx


class AdminSlugRedirectDeleteView(IsAdminMixin, DeleteView):
    model = SlugRedirect
    template_name = 'admin/seo/redirect_confirm_delete.html'
    success_url = reverse_lazy('management:seo_redirect_list')

    def form_valid(self, form):
        messages.success(self.request, "Redirect deleted successfully.")
        return super().form_valid(form)


# ── SEO Audit View ───────────────────────────────────────────────────────────
class AdminSEOAuditView(IsAdminMixin, TemplateView):
    template_name = 'admin/seo/audit.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from resources.models import ResourceItem

        # Only ResourceItem extends SEOModel — Page is a plain model without meta fields
        resources = ResourceItem.objects.select_related('vendor').only(
            'title', 'slug', 'meta_title', 'meta_description', 'meta_keywords', 'vendor'
        ).order_by('title')

        ctx['resources'] = resources
        ctx['resource_issues'] = sum(1 for r in resources if not r.meta_title or not r.meta_description)
        return ctx
