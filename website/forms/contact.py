"""
website/forms/contact.py
Contact form with honeypot field for bot protection.
"""
from django import forms
from phonenumber_field.formfields import PhoneNumberField

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Your full name", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "your@email.com", "autocomplete": "email"}),
    )
    phone = PhoneNumberField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "+254 7XX XXX XXX (optional)", "autocomplete": "tel"}),
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "How can we help?"}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Write your message here…", "rows": 5}),
    )
    # Honeypot — bots fill this, humans don't see it
    website_url = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_website_url(self):
        if self.cleaned_data.get("website_url"):
            raise forms.ValidationError("Bot detected.")
        return ""

