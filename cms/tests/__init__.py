from cms.tests.test_models import (
    TestCMSSiteSettingsCreation,
    TestCMSPageCreation,
    TestCMSMenuCreation,
    TestCMSMenuItemsCreation,
)
from cms.tests.test_views import TestCMSPageDetailView
from cms.tests.test_forms import MenuFormTests, SiteSettingFormTests, MenuItemFormTests
from cms.tests.test_utils import SlugToTitleTests, UniqueSlugGeneratorTests
from cms.tests.test_context_processors import (
    GlobalSettingsContextProcessorTests,
    GlobalSettingsViaClientTests,
)
from cms.tests.test_admin_views import (
    CMSAccessControlTests,
    AdminPageListViewTests,
    AdminPageCreateViewTests,
    AdminPageUpdateViewTests,
    AdminPageDeleteViewTests,
    AdminMenuListViewTests,
    AdminMenuCreateViewTests,
    AdminMenuUpdateViewTests,
    AdminMenuDeleteViewTests,
    AdminMenuItemListViewTests,
    AdminMenuItemCreateViewTests,
    AdminMenuItemUpdateViewTests,
    AdminMenuItemDeleteViewTests,
    AdminSiteSettingsListViewTests,
    AdminSiteSettingsCreateViewTests,
    AdminSiteSettingsUpdateViewTests,
    AdminSiteSettingsDeleteViewTests,
)

__all__ = [
    # Models
    "TestCMSSiteSettingsCreation",
    "TestCMSPageCreation",
    "TestCMSMenuCreation",
    "TestCMSMenuItemsCreation",
    # Public views
    "TestCMSPageDetailView",
    # Forms
    "MenuFormTests",
    "SiteSettingFormTests",
    "MenuItemFormTests",
    # Utils
    "SlugToTitleTests",
    "UniqueSlugGeneratorTests",
    # Context processors
    "GlobalSettingsContextProcessorTests",
    "GlobalSettingsViaClientTests",
    # Admin views
    "CMSAccessControlTests",
    "AdminPageListViewTests",
    "AdminPageCreateViewTests",
    "AdminPageUpdateViewTests",
    "AdminPageDeleteViewTests",
    "AdminMenuListViewTests",
    "AdminMenuCreateViewTests",
    "AdminMenuUpdateViewTests",
    "AdminMenuDeleteViewTests",
    "AdminMenuItemListViewTests",
    "AdminMenuItemCreateViewTests",
    "AdminMenuItemUpdateViewTests",
    "AdminMenuItemDeleteViewTests",
    "AdminSiteSettingsListViewTests",
    "AdminSiteSettingsCreateViewTests",
    "AdminSiteSettingsUpdateViewTests",
    "AdminSiteSettingsDeleteViewTests",
]
