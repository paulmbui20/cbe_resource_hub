from django import forms

from accounts.models import CustomUser


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "phone_number", "disable_email_notification"]
        widgets = {
            "disable_email_notification": forms.CheckboxInput(attrs={
                "class": "w-4 h-4 text-brand-primary bg-white/5 border-white/10 rounded focus:ring-brand-primary \
                         hover:cursor-pointer focus:ring-2"}),
        }
