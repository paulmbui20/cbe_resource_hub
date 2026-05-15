from django import forms
from website.models import BlogComment
from resources.models import ResourceComment

class AdminBlogCommentForm(forms.ModelForm):
    class Meta:
        model = BlogComment
        fields = ["page", "parent", "user", "name", "email", "body", "is_approved"]
        widgets = {
            "page": forms.Select(attrs={"class": "w-full rounded-lg bg-black/50 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "parent": forms.Select(attrs={"class": "w-full rounded-lg bg-black/50 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "user": forms.Select(attrs={"class": "w-full rounded-lg bg-black/50 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "name": forms.TextInput(attrs={"class": "w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "email": forms.EmailInput(attrs={"class": "w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "body": forms.Textarea(attrs={"class": "w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary", "rows": 5}),
            "is_approved": forms.CheckboxInput(attrs={"class": "w-4 h-4 text-brand-primary bg-white/5 border-white/10 rounded focus:ring-brand-primary focus:ring-2"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['page'].disabled = True
            # Also disable parent to prevent moving comments between threads in this view
            self.fields['parent'].disabled = True

class AdminResourceCommentForm(forms.ModelForm):
    class Meta:
        model = ResourceComment
        fields = ["resource", "parent", "user", "name", "email", "body", "is_approved"]
        widgets = {
            "resource": forms.Select(attrs={"class": "w-full rounded-lg bg-black/50 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "parent": forms.Select(attrs={"class": "w-full rounded-lg bg-black/50 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "user": forms.Select(attrs={"class": "w-full rounded-lg bg-black/50 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "name": forms.TextInput(attrs={"class": "w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "email": forms.EmailInput(attrs={"class": "w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary"}),
            "body": forms.Textarea(attrs={"class": "w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary", "rows": 5}),
            "is_approved": forms.CheckboxInput(attrs={"class": "w-4 h-4 text-brand-primary bg-white/5 border-white/10 rounded focus:ring-brand-primary focus:ring-2"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['resource'].disabled = True
            self.fields['parent'].disabled = True
