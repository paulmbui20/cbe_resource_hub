from website.tests.test_models import (
    ContactMessageModelTests,
    PartnerModelTests,
    EmailSubscriberModelTests,
    FAQModelTests,
    TestimonialModelTests,
)
from website.tests.test_forms import ContactFormTests, EmailSubscriptionFormTests
from website.tests.test_views import (
    HomePageViewTests,
    ContactViewTests,
    EmailSubscriptionViewTests,
    PartnerListViewTests,
    HealthCheckViewTests,
    FAQPageViewTests,
    TestimonialsPageViewTests,
    HomePageFAQTestimonialContextTests,
)
from website.tests.test_admin_views import (
    AdminWebsiteAccessControlTests,
    AdminDashboardViewTests,
    AdminContactMessageListViewTests,
    AdminContactMessageDetailViewTests,
    AdminContactMessageDeleteViewTests,
    AdminPartnerListViewTests,
    AdminPartnerCreateViewTests,
    AdminPartnerUpdateViewTests,
    AdminPartnerDeleteViewTests,
    AdminEmailSubscribersListViewTests,
    AdminEmailSubscriberCreateViewTests,
    AdminEmailSubscriberEditViewTests,
    AdminEmailSubscriberDeleteViewTests,
    AdminTestimonialListViewTests,
    AdminTestimonialCreateViewTests,
    AdminTestimonialUpdateViewTests,
    AdminTestimonialDeleteViewTests,
    AdminFAQListViewTests,
    AdminFAQCreateViewTests,
    AdminFAQUpdateViewTests,
    AdminFAQDeleteViewTests,
    AdminEmailSubscribersExportCSVViewTests,
    AdminBlogCommentListViewTests,
    AdminBlogCommentUpdateViewTests,
    AdminBlogCommentDeleteViewTests,
)
from website.tests.test_sitemaps import (
    StaticViewSitemapTests,
    PageSitemapTests,
    ResourceSitemapTests,
    ResourceTypeSitemapTests,
    GradeSitemapTests,
    LearningAreaSitemapTests,
    AcademicSessionSitemapTests,
    EducationLevelSitemapTests,
    PartnerSitemapTests,
    SitemapsRegistryTests,
)
from website.tests.test_cache import CacheInvalidationTests

from website.tests.test_sanitization import SanitizationTests

__all__ = [
    # Models
    "ContactMessageModelTests",
    "PartnerModelTests",
    "EmailSubscriberModelTests",
    "FAQModelTests",
    "TestimonialModelTests",
    # Forms
    "ContactFormTests",
    "EmailSubscriptionFormTests",
    # Public views
    "HomePageViewTests",
    "ContactViewTests",
    "EmailSubscriptionViewTests",
    "PartnerListViewTests",
    "HealthCheckViewTests",
    "FAQPageViewTests",
    "TestimonialsPageViewTests",
    "HomePageFAQTestimonialContextTests",
    # Admin views
    "AdminWebsiteAccessControlTests",
    "AdminDashboardViewTests",
    "AdminContactMessageListViewTests",
    "AdminContactMessageDetailViewTests",
    "AdminContactMessageDeleteViewTests",
    "AdminPartnerListViewTests",
    "AdminPartnerCreateViewTests",
    "AdminPartnerUpdateViewTests",
    "AdminPartnerDeleteViewTests",
    "AdminEmailSubscribersListViewTests",
    "AdminEmailSubscriberCreateViewTests",
    "AdminEmailSubscriberEditViewTests",
    "AdminEmailSubscriberDeleteViewTests",
    "AdminTestimonialListViewTests",
    "AdminTestimonialCreateViewTests",
    "AdminTestimonialUpdateViewTests",
    "AdminTestimonialDeleteViewTests",
    "AdminFAQListViewTests",
    "AdminFAQCreateViewTests",
    "AdminFAQUpdateViewTests",
    "AdminFAQDeleteViewTests",
    # Sitemaps
    "StaticViewSitemapTests",
    "PageSitemapTests",
    "ResourceSitemapTests",
    "ResourceTypeSitemapTests",
    "GradeSitemapTests",
    "LearningAreaSitemapTests",
    "AcademicSessionSitemapTests",
    "EducationLevelSitemapTests",
    "PartnerSitemapTests",
    "SitemapsRegistryTests",
    # Cache
    "CacheInvalidationTests",
    # Sanitization
    "SanitizationTests",
    # Email Subscribers Export CSV
    "AdminEmailSubscribersExportCSVViewTests",
    # Blog Comments
    "AdminBlogCommentListViewTests",
    "AdminBlogCommentUpdateViewTests",
    "AdminBlogCommentDeleteViewTests",
]
