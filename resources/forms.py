from django import forms
from .models import ResourceItem

class ResourceItemForm(forms.ModelForm):
    class Meta:
        model = ResourceItem
        fields = [
            'title', 'description', 
            'grade', 'learning_area', 
            'file', 'is_free', 'price'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary'}),
            'description': forms.Textarea(attrs={'class': 'w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary', 'rows': 4}),
            'grade': forms.Select(attrs={'class': 'w-full rounded-lg bg-black/50 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary'}),
            'learning_area': forms.Select(attrs={'class': 'w-full rounded-lg bg-black/50 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary'}),
            'file': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-white/70 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-white/10 file:text-white hover:file:bg-white/20'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-brand-primary bg-white/5 border-white/10 rounded focus:ring-brand-primary focus:ring-2'}),
            'price': forms.NumberInput(attrs={'class': 'w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white focus:ring-2 focus:ring-brand-primary'}),
        }
