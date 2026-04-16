"""resources/urls.py"""
from django.contrib.sitemaps.views import sitemap
from django.urls import path, re_path

from website.sitemaps import ResourceSitemap, ResourceTypeSitemap
from . import views

resources_sitemaps = {"resources": ResourceSitemap}
resources_types_sitemaps = {"resources_type": ResourceTypeSitemap}

app_name = "resources"

urlpatterns = [

    # endpoints for vendors
    path("add/", views.ResourceCreateView.as_view(), name="manage_add"),
    path("<slug:slug>/edit/", views.ResourceUpdateView.as_view(), name="manage_edit"),
    path("<slug:slug>/delete/", views.ResourceDeleteView.as_view(), name="manage_delete"),

    # public resources endpoints
    path("", views.ResourceListView.as_view(), name="list"),

    path("type/sitemap.xml", sitemap, {'sitemaps': resources_types_sitemaps}, name="type_sitemaps"),
    re_path(r'^type(?:/(?P<resource_type>[-\w]+))?/$', views.ResourceTypeDetailView.as_view(), name="type_detail"),

    re_path(r'^education-levels(?:/(?P<education_level>[-\w]+))?/$', views.EducationLevelDetailsView.as_view(),
            name="education_level_details"),

    re_path(r'^grades(?:/(?P<grade>[-\w]+))?/$', views.GradeDetailsView.as_view(), name="grade_details"),

    path("<slug:slug>/favorite/", views.ToggleFavoriteView.as_view(), name="toggle_favorite"),

    path('sitemap.xml', sitemap, {'sitemaps': resources_sitemaps}, name='resources_sitemap'),
    path("<slug:slug>/", views.ResourceDetailView.as_view(), name="resource_detail"),
    path("<slug:slug>/increment-downloads/", views.increment_downloads, name="resource_increment_downloads"),

]
