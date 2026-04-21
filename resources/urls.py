"""resources/urls.py"""
from django.contrib.sitemaps.views import sitemap
from django.urls import path, re_path

from website.sitemaps import ResourceSitemap, ResourceTypeSitemap, GradeSitemap, EducationLevelSitemap, \
    LearningAreaSitemap
from . import views

resources_sitemaps = {"resources": ResourceSitemap}
resources_types_sitemaps = {"resources_type": ResourceTypeSitemap}
grades_sitemaps = {"grades": GradeSitemap}
education_levels_sitemaps = {"education_levels": EducationLevelSitemap}
learning_areas_sitemaps = {"learning_areas": LearningAreaSitemap}

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

    path("education-levels/sitemap.xml", sitemap, {'sitemaps': education_levels_sitemaps},
         name="education_levels_sitemap"),
    re_path(r'^education-levels(?:/(?P<slug>[-\w]+))?/$', views.EducationLevelDetailsView.as_view(),
            name="education_level_details"),

    path("grades/", views.GradeListView.as_view(), name="grade_list"),
    path("grades/sitemap.xml", sitemap, {'sitemaps': grades_sitemaps}, name="grades_sitemaps"),
    re_path(r'^grades(?:/(?P<slug>[-\w]+))?/$', views.GradeDetailsView.as_view(), name="grade_details"),

    path("learning-areas/sitemap.xml", sitemap, {'sitemaps': learning_areas_sitemaps},
         name="learning_areas_sitemap"),
    path("learning-areas/", views.LearningAreaListView.as_view(), name="learning_areas_list"),
    re_path(r'learning-areas(?:/(?P<slug>[-\w]+))?/$', views.LearningAreaDetailsView.as_view(),
            name="learning_area_details"),

    path("<slug:slug>/favorite/", views.ToggleFavoriteView.as_view(), name="toggle_favorite"),

    path('sitemap.xml', sitemap, {'sitemaps': resources_sitemaps}, name='resources_sitemap'),
    path("<slug:slug>/", views.ResourceDetailView.as_view(), name="resource_detail"),
    path("<slug:slug>/increment-downloads/", views.increment_downloads, name="resource_increment_downloads"),

]
