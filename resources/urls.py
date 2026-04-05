"""resources/urls.py"""
from django.urls import path

from . import views

app_name = "resources"

urlpatterns = [
    path("", views.ResourceListView.as_view(), name="list"),
    path("manage/add/", views.ResourceCreateView.as_view(), name="manage_add"),
    path("manage/<slug:slug>/edit/", views.ResourceUpdateView.as_view(), name="manage_edit"),
    path("manage/<slug:slug>/delete/", views.ResourceDeleteView.as_view(), name="manage_delete"),
    path("<slug:slug>/favorite/", views.ToggleFavoriteView.as_view(), name="toggle_favorite"),
    path("<slug:slug>/", views.ResourceDetailView.as_view(), name="resource_detail"),
]
