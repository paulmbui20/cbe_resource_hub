from core.tests.test_models import (
    TermModelTests,
    YearModelTests,
    AcademicSessionModelTests,
    TimeStampedModelTests,
)
from core.tests.test_utils import CurrentYearTests, ClearObjectCacheTests
from core.tests.test_signals import (
    AcademicSessionSignalTests,
    TermSignalTests,
    YearSignalTests,
)
from core.tests.test_admin_views import (
    CoreAccessControlTests,
    AdminYearListViewTests,
    AdminYearCreateViewTests,
    AdminYearUpdateViewTests,
    AdminYearDeleteViewTests,
    AdminTermListViewTests,
    AdminTermCreateViewTests,
    AdminTermUpdateViewTests,
    AdminTermDeleteViewTests,
    AdminAcademicSessionListViewTests,
    AdminAcademicSessionCreateViewTests,
    AdminAcademicSessionUpdateViewTests,
    AdminAcademicSessionDeleteViewTests,
)

__all__ = [
    # Models
    "TermModelTests",
    "YearModelTests",
    "AcademicSessionModelTests",
    "TimeStampedModelTests",
    # Utils
    "CurrentYearTests",
    "ClearObjectCacheTests",
    # Signals
    "AcademicSessionSignalTests",
    "TermSignalTests",
    "YearSignalTests",
    # Admin views
    "CoreAccessControlTests",
    "AdminYearListViewTests",
    "AdminYearCreateViewTests",
    "AdminYearUpdateViewTests",
    "AdminYearDeleteViewTests",
    "AdminTermListViewTests",
    "AdminTermCreateViewTests",
    "AdminTermUpdateViewTests",
    "AdminTermDeleteViewTests",
    "AdminAcademicSessionListViewTests",
    "AdminAcademicSessionCreateViewTests",
    "AdminAcademicSessionUpdateViewTests",
    "AdminAcademicSessionDeleteViewTests",
]
