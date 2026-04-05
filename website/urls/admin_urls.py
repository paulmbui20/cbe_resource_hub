from django.urls import path
from website import admin_views as views

app_name = "management"

urlpatterns = [
    # Dashboard
    path("", views.AdminDashboardView.as_view(), name="dashboard"),
    
    # Users
    path("users/", views.AdminUserListView.as_view(), name="user_list"),
    path("users/<int:pk>/edit/", views.AdminUserUpdateView.as_view(), name="user_edit"),
    
    # Pages
    path("pages/", views.AdminPageListView.as_view(), name="page_list"),
    path("pages/add/", views.AdminPageCreateView.as_view(), name="page_add"),
    path("pages/<int:pk>/edit/", views.AdminPageUpdateView.as_view(), name="page_edit"),
    path("pages/<int:pk>/delete/", views.AdminPageDeleteView.as_view(), name="page_delete"),
    
    # Menus
    path("menus/", views.AdminMenuListView.as_view(), name="menu_list"),
    path("menus/<int:pk>/edit/", views.AdminMenuUpdateView.as_view(), name="menu_edit"),
    
    # Settings
    path("settings/", views.AdminSiteSettingsListView.as_view(), name="settings_list"),
    path("settings/<int:pk>/edit/", views.AdminSiteSettingsUpdateView.as_view(), name="settings_edit"),
    
    # Resources (Read-only list, management actions go to regular edit)
    path("resources/", views.AdminResourceListView.as_view(), name="resource_list"),
]
