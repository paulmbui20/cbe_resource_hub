from tinymce.models import HTMLField
from django_nh3.models import Nh3FieldMixin

class SafeHTMLField(Nh3FieldMixin, HTMLField):
    """
    An HTMLField that automatically sanitizes its content using django-nh3
    before saving to the database, while still using the TinyMCE widget in forms.
    """
    pass
