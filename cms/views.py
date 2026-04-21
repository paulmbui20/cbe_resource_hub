"""cms/views.py"""

from django.views.generic import DetailView

from .models import Page


class PageDetailView(DetailView):
    template_name = "cms/page_detail.html"
    context_object_name = "page"

    def get_queryset(self):
        return Page.objects.filter(is_published=True)
