from .test_adapters import (
    SlugifyUsernameTests, UniqueUsernameTests, AccountAdapterPopulateUsernameTests,
    AccountAdapterSaveUserTests, SocialAccountAdapterPreSocialLoginTests, SocialAccountAdapterPopulateUserTests,
)
from .test_admin_views import (
    IsAdminMixinTests, AdminUserListViewTests, AdminUserCreateViewTests, AdminUserUpdateViewTests,
    AdminUserDeleteViewTests, AdminUserBulkToggleViewTests
)
from .test_django_admin import (
    CustomUserAdminRegistrationTests, CustomUserAdminConfigTests, CustomUserAdminChangelistTests,
    CustomUserAdminChangeFormTests, CustomUserAdminAddFormTests,
)
from .test_forms import ProfileFormTestCase
from .test_models import TestUserCreation
from .test_signals import (
    EnsureSuperuserEmailVerifiedTests, ResetMustChangePasswordTests, GenerateUsernameFromEmailTests
)
from .test_views import (
    AccountsProfileViewTests, AccountsBecomeVendorViewTests, AccountsDashboardViewTests
)

__all__ = [
    "TestUserCreation",
    "ProfileFormTestCase",
    "AccountsProfileViewTests",
    "AccountsBecomeVendorViewTests",
    "AccountsDashboardViewTests",
    "IsAdminMixinTests",
    "AdminUserListViewTests",
    "AdminUserCreateViewTests",
    "AdminUserUpdateViewTests",
    "AdminUserDeleteViewTests",
    "AdminUserBulkToggleViewTests",
    "EnsureSuperuserEmailVerifiedTests",
    "ResetMustChangePasswordTests",
    "GenerateUsernameFromEmailTests",
    "SlugifyUsernameTests",
    "UniqueUsernameTests",
    "AccountAdapterPopulateUsernameTests",
    "AccountAdapterSaveUserTests",
    "SocialAccountAdapterPreSocialLoginTests",
    "SocialAccountAdapterPopulateUserTests",
    "CustomUserAdminRegistrationTests",
    "CustomUserAdminConfigTests",
    "CustomUserAdminChangelistTests",
    "CustomUserAdminChangeFormTests",
    "CustomUserAdminAddFormTests",
]
