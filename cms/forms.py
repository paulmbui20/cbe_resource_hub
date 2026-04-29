from django import forms
from cms.models import Menu, SiteSetting, MenuItem

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'list': 'menu_names_list',
                'placeholder': 'e.g. Primary Header, Footer...'
            }),
        }

class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = ['key', 'value']
        widgets = {
            'key': forms.TextInput(attrs={
                'list': 'setting_keys_list',
                'placeholder': 'e.g. site_name, contact_email...',
                'x-model': 'settingKey',
            }),
            'value': forms.Textarea(attrs={
                'rows': 4,
                'x-show': 'settingKey !== "site_indexing"',
                ':required': 'settingKey !== "site_indexing"',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We handle site_indexing custom UI via a secondary input that mirrors to value.
        # However, to avoid form validation errors if 'value' is disabled, django requires the value to be present.
        # We will handle it by keeping the textarea enabled but visually hidden, and synced via Alpine, OR
        # just letting Alpine sync the value to the hidden actual textarea.
        # Actually, simpler: make value a text input but Alpine syncs it.
        # Let's use a hidden input or text area and a custom visible select in the template.
        self.fields['value'].widget.attrs.update({
            'x-show': "settingKey !== 'site_indexing'",
            'x-ref': 'realValueInput',
        })

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = '__all__'
        widgets = {
            'url': forms.TextInput(attrs={
                'list': 'menuitem_urls_list',
                'placeholder': 'e.g. /resources/ or https://...',
            }),
        }
