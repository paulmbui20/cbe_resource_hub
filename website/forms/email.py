from django import forms

from website.models import EmailSubscriber


class EmailSubscriptionForm(forms.ModelForm):
    honeypot = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"style": "display:none;", "tabindex": "-1", "autocomplete": "off"}
        ),
    )

    class Meta:
        model = EmailSubscriber
        fields = ["email", "full_name"]

    def clean(self):
        cleaned_data = super().clean()
        honeypot = cleaned_data.get("honeypot")
        if honeypot:
            # If the honeypot has any value, it's a bot
            raise forms.ValidationError("Invalid submission detected.")
        return cleaned_data
