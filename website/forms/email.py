from django import forms

from website.models import EmailSubscriber


class EmailSubscriptionForm(forms.ModelForm):
    class Meta:
        model = EmailSubscriber
        fields = ['email', 'full_name']
