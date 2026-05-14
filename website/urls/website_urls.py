from django.urls import path

from website.health_checks import health_check, liveness_check, readiness_check, celery_health
from website.views import (
    HomePageView,
    ContactView,
    PartnerListView,
    FAQPageView,
    TestimonialsPageView,
    email_subscription,
    blog_comment_post,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("email-subscription/", email_subscription, name="email_subscription"),
    path("partners/", PartnerListView.as_view(), name="partners"),
    path("faqs/", FAQPageView.as_view(), name="faqs"),
    path("testimonials/", TestimonialsPageView.as_view(), name="testimonials"),

    # Blog comment HTMX endpoint
    path(
        "blog/<int:page_id>/comment/",
        blog_comment_post,
        name="blog_comment_post",
    ),

    # Health check endpoints
    path('health/', health_check, name='health_check'),
    path('health/live/', liveness_check, name='liveness'),
    path('health/ready/', readiness_check, name='readiness'),
    path('health/celery/', celery_health, name='celery_health'),
]
