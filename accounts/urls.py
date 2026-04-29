"""accounts/urls.py"""
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("profile/",   views.ProfileView.as_view(),   name="profile"),
    path("become-vendor/", views.BecomeVendorView.as_view(), name="become_vendor"),
]
