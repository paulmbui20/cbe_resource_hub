from django import forms

from seo.models import SlugRedirect


# ── SlugRedirect Form ────────────────────────────────────────────────────────
class SlugRedirectForm(forms.ModelForm):
    class Meta:
        model = SlugRedirect
        fields = ['old_slug', 'new_slug']
        widgets = {
            'old_slug': forms.Textarea(attrs={
                'class': 'w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary transition-all',
                'placeholder': 'e.g. old-page-name',
                'rows': '3'
            }),
            'new_slug': forms.Textarea(attrs={
                'class': 'w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary transition-all',
                'placeholder': 'e.g. new-page-name',
                'rows': '3'
            }),
        }
        help_texts = {
            'old_slug': 'The old URL slug that should be redirected (e.g. my-old-post)',
            'new_slug': 'The new URL slug to redirect traffic to (e.g. my-new-post)',
        }
