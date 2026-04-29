from django.urls import path

from core.admin_views import AdminYearListView, AdminYearUpdateView, AdminYearDeleteView, AdminYearCreateView, \
    AdminTermListView, AdminTermCreateView, AdminTermUpdateView, AdminTermDeleteView, AdminAcademicSessionListView, \
    AdminAcademicSessionCreateView, AdminAcademicSessionUpdateView, AdminAcademicSessionDeleteView

urlpatterns = [
    # Years Admin Crud
    path("years/", AdminYearListView.as_view(), name="year_list"),
    path("years/create/", AdminYearCreateView.as_view(), name="year_create"),
    path("years/<int:pk>/update/", AdminYearUpdateView.as_view(), name="year_update"),
    path("years/<int:pk>/delete/", AdminYearDeleteView.as_view(), name="year_delete"),

    # Terms
    path("terms/", AdminTermListView.as_view(), name="term_list"),
    path("terms/create/", AdminTermCreateView.as_view(), name="term_create"),
    path("terms/<int:pk>/update/", AdminTermUpdateView.as_view(), name="term_update"),
    path("terms/<int:pk>/delete/", AdminTermDeleteView.as_view(), name="term_delete"),

    # Academic Sessions
    path("academic-sessions/", AdminAcademicSessionListView.as_view(), name="academic_session_list"),
    path("academic-sessions/create/", AdminAcademicSessionCreateView.as_view(), name="academic_session_create"),
    path("academic-sessions/<int:pk>/update", AdminAcademicSessionUpdateView.as_view(), name="academic_session_update"),
    path("academic-sessions/<int:pk>/delete", AdminAcademicSessionDeleteView.as_view(), name="academic_session_delete"),
]
