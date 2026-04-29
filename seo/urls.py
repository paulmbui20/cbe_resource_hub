from django.urls import path

from seo import admin_views

urlpatterns = [
    # SEO Management
    path("slug-redirects/", admin_views.AdminSlugRedirectListView.as_view(), name="seo_redirect_list"),
    path("add/", admin_views.AdminSlugRedirectCreateView.as_view(), name="seo_redirect_add"),
    path("<int:pk>/edit/", admin_views.AdminSlugRedirectUpdateView.as_view(), name="seo_redirect_edit"),
    path("<int:pk>/delete/", admin_views.AdminSlugRedirectDeleteView.as_view(), name="seo_redirect_delete"),

    path("pages/audit/", admin_views.AdminPagesSEOAuditView.as_view(), name="pages_seo_audit"),
    path("resources/audit/", admin_views.AdminResourcesSEOAuditView.as_view(), name="resources_seo_audit"),

]
