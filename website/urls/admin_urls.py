from django.urls import path, include

from website import admin_views as views

app_name = "management"

urlpatterns = [
    # Dashboard
    path("", views.AdminDashboardView.as_view(), name="dashboard"),

    # CMS eg pages, menus, and settings
    path("cms/", include("cms.admin_urls")),

    # Core app models like Year, Term, AcademicSession
    path("core/", include("core.admin_urls")),

    # Files
    path("files/", include("files.admin_urls")),

    # Notifications
    path("notifications/", include("notifications.urls")),

    # Resources (Read-only list, management actions go to regular edit)
    path("resources/", include("resources.admin_urls")),

    # Seo
    path("seo/", include("seo.urls")),

    # Users
    path("users/", include("accounts.admin_urls")),

    # Contact Messages
    path("contacts/", views.AdminContactMessageListView.as_view(), name="contact_list"),
    path("contacts/<int:pk>/", views.AdminContactMessageDetailView.as_view(), name="contact_detail"),
    path("contacts/<int:pk>/delete/", views.AdminContactMessageDeleteView.as_view(), name="contact_delete"),

    # Email Subscribers
    path('email-subscribers/', views.AdminEmailSubscribersListView.as_view(), name='email_subscribers'),
    path('email-subscribers/add/', views.AdminEmailSubscribersCreateView.as_view(), name='email_subscriber_add'),
    path('email-subscribers/<int:pk>/update', views.AdminEmailSubscriberEdit.as_view(), name='email_subscriber_edit'),
    path('email-subscribers/<int:pk>/delete/', views.AdminEmailSubscriberDeleteView.as_view(),
         name='email_subscribers_delete'),

    # Partners
    path("partners/", views.AdminPartnerListView.as_view(), name="partner_list"),
    path("partners/add/", views.AdminPartnerCreateView.as_view(), name="partner_add"),
    path("partners/<int:pk>/edit/", views.AdminPartnerUpdateView.as_view(), name="partner_edit"),
    path("partners/<int:pk>/delete/", views.AdminPartnerDeleteView.as_view(), name="partner_delete"),

    # Testimonials
    path("testimonials/", views.AdminTestimonialListView.as_view(), name="testimonial_list"),
    path("testimonials/add/", views.AdminTestimonialCreateView.as_view(), name="testimonial_add"),
    path("testimonials/<int:pk>/edit/", views.AdminTestimonialUpdateView.as_view(), name="testimonial_edit"),
    path("testimonials/<int:pk>/delete/", views.AdminTestimonialDeleteView.as_view(), name="testimonial_delete"),

    # FAQs
    path("faqs/", views.AdminFAQListView.as_view(), name="faq_list"),
    path("faqs/add/", views.AdminFAQCreateView.as_view(), name="faq_add"),
    path("faqs/<int:pk>/edit/", views.AdminFAQUpdateView.as_view(), name="faq_edit"),
    path("faqs/<int:pk>/delete/", views.AdminFAQDeleteView.as_view(), name="faq_delete"),

]
