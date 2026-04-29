from seo.tests.test_models import (
    PublicFilesStorageCallableTests,
    SEOModelFieldTests,
    SEOModelMethodTests,
    SlugRedirectCreationTests,
    SlugRedirectGetRedirectTests,
    SlugRedirectCreateRedirectTests,
    SlugRedirectClearForSlugTests,
)
from seo.tests.test_mixins import SlugRedirectMixinTests
from seo.tests.test_middleware import SlugRedirectMiddlewareTests
from seo.tests.test_utils import GenerateMetaDescriptionTests, GenerateKeywordsTests
from seo.tests.test_forms import SlugRedirectFormTests
from seo.tests.test_admin_views import (
    SEOAdminAccessControlTests,
    AdminSlugRedirectListViewTests,
    AdminSlugRedirectCreateViewTests,
    AdminSlugRedirectUpdateViewTests,
    AdminSlugRedirectDeleteViewTests,
    AdminPagesSEOAuditViewTests,
    AdminResourcesSEOAuditViewTests,
)

__all__ = [
    # Models
    "PublicFilesStorageCallableTests",
    "SEOModelFieldTests",
    "SEOModelMethodTests",
    "SlugRedirectCreationTests",
    "SlugRedirectGetRedirectTests",
    "SlugRedirectCreateRedirectTests",
    "SlugRedirectClearForSlugTests",
    # Mixins
    "SlugRedirectMixinTests",
    # Middleware
    "SlugRedirectMiddlewareTests",
    # Utils
    "GenerateMetaDescriptionTests",
    "GenerateKeywordsTests",
    # Forms
    "SlugRedirectFormTests",
    # Admin views
    "SEOAdminAccessControlTests",
    "AdminSlugRedirectListViewTests",
    "AdminSlugRedirectCreateViewTests",
    "AdminSlugRedirectUpdateViewTests",
    "AdminSlugRedirectDeleteViewTests",
    "AdminPagesSEOAuditViewTests",
    "AdminResourcesSEOAuditViewTests",
]
