from django.urls import path

from resources import admin_views
from resources import admin_dependency_views as dep_views


urlpatterns = [

    # endpoints for admins
    path("", admin_views.AdminResourceListView.as_view(), name="resource_list"),
    path("add/", admin_views.AdminResourceCreateView.as_view(), name="resource_add"),
    path("<int:pk>/edit/", admin_views.AdminResourceUpdateView.as_view(), name="resource_edit"),
    path("<int:pk>/delete/", admin_views.AdminResourceDeleteView.as_view(), name="resource_delete"),

    # Levels
    path("levels/", dep_views.AdminEducationLevelListView.as_view(), name="level_list"),
    path("levels/add/", dep_views.AdminEducationLevelCreateView.as_view(), name="level_add"),
    path("levels/<int:pk>/edit/", dep_views.AdminEducationLevelUpdateView.as_view(), name="level_edit"),
    path("levels/<int:pk>/delete/", dep_views.AdminEducationLevelDeleteView.as_view(), name="level_delete"),

    # Grades
    path("grades/", dep_views.AdminGradeListView.as_view(), name="grade_list"),
    path("grades/add/", dep_views.AdminGradeCreateView.as_view(), name="grade_add"),
    path("grades/<int:pk>/edit/", dep_views.AdminGradeUpdateView.as_view(), name="grade_edit"),
    path("grades/<int:pk>/delete/", dep_views.AdminGradeDeleteView.as_view(), name="grade_delete"),

    # Learning Areas
    path("learningareas/", dep_views.AdminLearningAreaListView.as_view(), name="learningarea_list"),
    path("learningareas/add/", dep_views.AdminLearningAreaCreateView.as_view(), name="learningarea_add"),
    path("learningareas/<int:pk>/edit/", dep_views.AdminLearningAreaUpdateView.as_view(), name="learningarea_edit"),
    path("learningareas/<int:pk>/delete/", dep_views.AdminLearningAreaDeleteView.as_view(), name="learningarea_delete"),


]
