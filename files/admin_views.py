from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, View

from accounts.admin_views import IsAdminMixin
from .models import File


class AdminFileListView(IsAdminMixin, ListView):
    model = File
    template_name = "admin/files/file_list.html"
    context_object_name = "files"
    paginate_by = 40

    def get_queryset(self):
        qs = File.objects.all().order_by("-created")
        category = self.request.GET.get('category')
        q = self.request.GET.get('q')

        if category and category != 'all':
            qs = qs.filter(file_category=category)
        if q:
            qs = qs.filter(title__icontains=q)

        return qs

    def get_template_names(self):
        # Return the partial grid structure if this is an HTMX targeted swap
        if self.request.headers.get('HX-Request'):
            return ["admin/files/partials/grid.html"]
        return [self.template_name]


class AdminFileUploadView(IsAdminMixin, View):
    def post(self, request, *args, **kwargs):
        uploaded_files = request.FILES.getlist('file')

        for f in uploaded_files:
            # We use the original filename as the initial title safely
            title = getattr(f, 'name', 'Untitled')[:250]
            File.objects.create(title=title, file=f)

        # Returning a 204 No Content response but injecting an HTMX trigger
        # to make the main grid dynamically reload its layout.
        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'mediaUpdated'
        return response


class AdminFileUpdateView(IsAdminMixin, View):
    def post(self, request, pk, *args, **kwargs):
        file_obj = get_object_or_404(File, pk=pk)

        title = request.POST.get('title')
        if title:
            file_obj.title = title
            file_obj.save(update_fields=['title'])

        response = HttpResponse("Saved", status=200)
        # We explicitly trigger a refresh so the title updates on grid hover overlays
        response['HX-Trigger'] = 'mediaUpdated'
        return response


class AdminFileDeleteView(IsAdminMixin, View):
    def post(self, request, pk, *args, **kwargs):
        file_obj = get_object_or_404(File, pk=pk)
        title = file_obj.title or f"File #{pk}"
        file_obj.delete()

        from django.contrib import messages
        from django.shortcuts import redirect
        messages.success(request, f'"{title}" has been permanently deleted.')
        return redirect("management:file_list")
