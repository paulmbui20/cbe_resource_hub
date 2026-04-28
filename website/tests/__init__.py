from website.tests.test_models import (
    ContactMessageModelTests,
    PartnerModelTests,
    EmailSubscriberModelTests,
)
from website.tests.test_forms import ContactFormTests, EmailSubscriptionFormTests
from website.tests.test_views import (
    HomePageViewTests,
    ContactViewTests,
    EmailSubscriptionViewTests,
    PartnerListViewTests,
    HealthCheckViewTests,
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

__all__ = [
    # Models
    "ContactMessageModelTests",
    "PartnerModelTests",
    "EmailSubscriberModelTests",
    # Forms
    "ContactFormTests",
    "EmailSubscriptionFormTests",
    # Public views
    "HomePageViewTests",
    "ContactViewTests",
    "EmailSubscriptionViewTests",
    "PartnerListViewTests",
    "HealthCheckViewTests",
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
]
