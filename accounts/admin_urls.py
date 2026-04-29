from django.urls import path

from accounts import admin_views

urlpatterns = [

    path("", admin_views.AdminUserListView.as_view(), name="user_list"),
    path("add/", admin_views.AdminUserCreateView.as_view(), name="user_add"),
    path("bulk-toggle/", admin_views.AdminUserBulkToggleView.as_view(), name="user_bulk_toggle"),
    path("<int:pk>/edit/", admin_views.AdminUserUpdateView.as_view(), name="user_edit"),
    path("<int:pk>/delete/", admin_views.AdminUserDeleteView.as_view(), name="user_delete"),

]
