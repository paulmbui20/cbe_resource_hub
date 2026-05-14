"""
website/forms/comment.py

Blog comment form. For authenticated users only the `body` field is shown;
anonymous users must also supply `name` and `email`.
"""

import re

from django import forms


class BlogCommentForm(forms.Form):
    """
    Generic comment form.  The view decides which fields to render/validate
    based on whether the current user is authenticated.
    """

    # Anonymous-only fields (hidden / pre-filled for auth users)
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Your name",
                "autocomplete": "name",
                "class": "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-white/30 focus:outline-none focus:border-brand-gold/60 focus:ring-1 focus:ring-brand-gold/40 transition-colors",
            }
        ),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "your@email.com (not shown publicly)",
                "autocomplete": "email",
                "class": "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-white/30 focus:outline-none focus:border-brand-gold/60 focus:ring-1 focus:ring-brand-gold/40 transition-colors",
            }
        ),
    )
    body = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Share your thoughts…",
                "class": "w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-white/30 focus:outline-none focus:border-brand-gold/60 focus:ring-1 focus:ring-brand-gold/40 transition-colors resize-none",
            }
        ),
    )
    # Honeypot anti-spam field — must stay empty
    website_url = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean_website_url(self):
        """Reject submissions where bots fill the honeypot field."""
        value = self.cleaned_data.get("website_url", "")
        if value:
            raise forms.ValidationError("Invalid submission detected.")
        return value

    def clean_body(self):
        body = self.cleaned_data.get("body", "")
        # Strip dangerous patterns while preserving plain text
        body = body.strip()
        if len(body) < 3:
            raise forms.ValidationError("Comment is too short.")
        # Rudimentary spam filter: more than 5 URLs → reject
        url_count = len(re.findall(r"https?://", body))
        if url_count > 5:
            raise forms.ValidationError(
                "Comments with many links are not allowed."
            )
        return body

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if len(name) < 2:
            raise forms.ValidationError("Please enter your full name.")
        return name
