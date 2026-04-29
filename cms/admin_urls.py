from django.urls import path

from cms import admin_views

urlpatterns = [

    # Pages
    path("pages/", admin_views.AdminPageListView.as_view(), name="page_list"),
    path("pages/add/", admin_views.AdminPageCreateView.as_view(), name="page_add"),
    path("pages/<int:pk>/edit/", admin_views.AdminPageUpdateView.as_view(), name="page_edit"),
    path("pages/<int:pk>/delete/", admin_views.AdminPageDeleteView.as_view(), name="page_delete"),

    # Menus
    path("menus/", admin_views.AdminMenuListView.as_view(), name="menu_list"),
    path("menus/add/", admin_views.AdminMenuCreateView.as_view(), name="menu_add"),
    path("menus/<int:pk>/edit/", admin_views.AdminMenuUpdateView.as_view(), name="menu_edit"),
    path("menus/<int:pk>/delete/", admin_views.AdminMenuDeleteView.as_view(), name="menu_delete"),

    # Menu Items
    path("menu-items/", admin_views.AdminMenuItemListView.as_view(), name="menuitem_list"),
    path("menu-items/add/", admin_views.AdminMenuItemCreateView.as_view(), name="menuitem_add"),
    path("menu-items/<int:pk>/edit/", admin_views.AdminMenuItemUpdateView.as_view(), name="menuitem_edit"),
    path("menu-items/<int:pk>/delete/", admin_views.AdminMenuItemDeleteView.as_view(), name="menuitem_delete"),

    # Settings
    path("settings/", admin_views.AdminSiteSettingsListView.as_view(), name="settings_list"),
    path("settings/add/", admin_views.AdminSiteSettingsCreateView.as_view(), name="settings_add"),
    path("settings/<int:pk>/edit/", admin_views.AdminSiteSettingsUpdateView.as_view(), name="settings_edit"),
    path("settings/<int:pk>/delete/", admin_views.AdminSiteSettingsDeleteView.as_view(), name="settings_delete"),

]
