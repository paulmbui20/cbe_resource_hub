from django.urls import path
from website import admin_views as views
from website import admin_dependency_views as dep_views
from files import views as file_views
from seo import admin_views as seo_views

app_name = "management"

urlpatterns = [
    # Dashboard
    path("", views.AdminDashboardView.as_view(), name="dashboard"),
    
    # Users
    path("users/", views.AdminUserListView.as_view(), name="user_list"),
    path("users/add/", views.AdminUserCreateView.as_view(), name="user_add"),
    path("users/bulk-toggle/", views.AdminUserBulkToggleView.as_view(), name="user_bulk_toggle"),
    path("users/<int:pk>/edit/", views.AdminUserUpdateView.as_view(), name="user_edit"),
    path("users/<int:pk>/delete/", views.AdminUserDeleteView.as_view(), name="user_delete"),
    
    # Pages
    path("pages/", views.AdminPageListView.as_view(), name="page_list"),
    path("pages/add/", views.AdminPageCreateView.as_view(), name="page_add"),
    path("pages/<int:pk>/edit/", views.AdminPageUpdateView.as_view(), name="page_edit"),
    path("pages/<int:pk>/delete/", views.AdminPageDeleteView.as_view(), name="page_delete"),
    
    # Menus
    path("menus/", views.AdminMenuListView.as_view(), name="menu_list"),
    path("menus/add/", views.AdminMenuCreateView.as_view(), name="menu_add"),
    path("menus/<int:pk>/edit/", views.AdminMenuUpdateView.as_view(), name="menu_edit"),
    path("menus/<int:pk>/delete/", views.AdminMenuDeleteView.as_view(), name="menu_delete"),
    
    # Settings
    path("settings/", views.AdminSiteSettingsListView.as_view(), name="settings_list"),
    path("settings/add/", views.AdminSiteSettingsCreateView.as_view(), name="settings_add"),
    path("settings/<int:pk>/edit/", views.AdminSiteSettingsUpdateView.as_view(), name="settings_edit"),
    path("settings/<int:pk>/delete/", views.AdminSiteSettingsDeleteView.as_view(), name="settings_delete"),
    
    # Resources (Read-only list, management actions go to regular edit)
    path("resources/", views.AdminResourceListView.as_view(), name="resource_list"),
    path("resources/add/", views.AdminResourceCreateView.as_view(), name="resource_add"),
    path("resources/<int:pk>/edit/", views.AdminResourceUpdateView.as_view(), name="resource_edit"),
    path("resources/<int:pk>/delete/", views.AdminResourceDeleteView.as_view(), name="resource_delete"),

    # Media Library (Files Management)
    path("files/", file_views.AdminFileListView.as_view(), name="file_list"),
    path("files/upload/", file_views.AdminFileUploadView.as_view(), name="file_upload"),
    path("files/<int:pk>/", file_views.AdminFileUpdateView.as_view(), name="file_edit"),
    path("files/<int:pk>/delete/", file_views.AdminFileDeleteView.as_view(), name="file_delete"),

    # Dependencies (Imported directly in file to avoid bloat)


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
    
    # Menu Items
    path("menuitems/", dep_views.AdminMenuItemListView.as_view(), name="menuitem_list"),
    path("menuitems/add/", dep_views.AdminMenuItemCreateView.as_view(), name="menuitem_add"),
    path("menuitems/<int:pk>/edit/", dep_views.AdminMenuItemUpdateView.as_view(), name="menuitem_edit"),
    path("menuitems/<int:pk>/delete/", dep_views.AdminMenuItemDeleteView.as_view(), name="menuitem_delete"),

    # Contact Messages
    path("contacts/", views.AdminContactMessageListView.as_view(), name="contact_list"),
    path("contacts/<int:pk>/", views.AdminContactMessageDetailView.as_view(), name="contact_detail"),
    path("contacts/<int:pk>/delete/", views.AdminContactMessageDeleteView.as_view(), name="contact_delete"),

    # SEO Management
    path("seo/", seo_views.AdminSlugRedirectListView.as_view(), name="seo_redirect_list"),
    path("seo/add/", seo_views.AdminSlugRedirectCreateView.as_view(), name="seo_redirect_add"),
    path("seo/<int:pk>/edit/", seo_views.AdminSlugRedirectUpdateView.as_view(), name="seo_redirect_edit"),
    path("seo/<int:pk>/delete/", seo_views.AdminSlugRedirectDeleteView.as_view(), name="seo_redirect_delete"),
    path("seo/audit/", seo_views.AdminSEOAuditView.as_view(), name="seo_audit"),

    # Partners
    path("partners/", views.AdminPartnerListView.as_view(), name="partner_list"),
    path("partners/add/", views.AdminPartnerCreateView.as_view(), name="partner_add"),
    path("partners/<int:pk>/edit/", views.AdminPartnerUpdateView.as_view(), name="partner_edit"),
    path("partners/<int:pk>/delete/", views.AdminPartnerDeleteView.as_view(), name="partner_delete"),

    # Notifications
    path("notifications/", views.AdminNotificationListView.as_view(), name="notification_list"),
    path("notifications/<int:pk>/retry/", views.AdminNotificationRetryView.as_view(), name="notification_retry"),
]
