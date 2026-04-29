from django.urls import path

from files import admin_views

urlpatterns = [

    # Media Library (Files Management)
    path("", admin_views.AdminFileListView.as_view(), name="file_list"),
    path("upload/", admin_views.AdminFileUploadView.as_view(), name="file_upload"),
    path("<int:pk>/", admin_views.AdminFileUpdateView.as_view(), name="file_edit"),
    path("<int:pk>/delete/", admin_views.AdminFileDeleteView.as_view(), name="file_delete"),

]
