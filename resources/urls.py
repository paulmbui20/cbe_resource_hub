"""resources/urls.py"""
from django.urls import path

from . import views

app_name = "resources"

urlpatterns = [
    path("", views.ResourceListView.as_view(), name="list"),
    path("<slug:slug>/", views.ResourceDetailView.as_view(), name="resource_detail"),
]
