from resources.tests.test_models import (
    EducationLevelModelTests,
    GradeModelTests,
    LearningAreaModelTests,
    ResourceItemModelTests,
)
from resources.tests.test_forms import ResourceItemFormTests
from resources.tests.test_cache import (
    GetLearningAreasTests,
    GetGradesTests,
    GetEducationLevelsTests,
    GetResourceTypesTests,
    GetSlugBasedObjectTests,
    GetAcademicSessionsTests,
)
from resources.tests.test_signals import (
    LearningAreaSignalTests,
    GradeSignalTests,
    EducationLevelSignalTests,
)
from resources.tests.test_utils import (
    GetYearAndMonthTests,
    FileUploadPathTests,
    PublicFilesStorageCallableTests,
)
from resources.tests.test_views import (
    ResourceListViewTests,
    ResourceDetailViewTests,
    IncrementDownloadsViewTests,
    ToggleFavoriteViewTests,
    ResourceTypeDetailViewTests,
    EducationLevelDetailsViewTests,
    LearningAreaDetailsViewTests,
    GradeDetailsViewTests,
    AcademicSessionDetailViewTests,
    LearningAreaListViewTests,
    GradeListViewTests,
    AcademicSessionListViewTests,
    ResourceCreateViewTests,
    ResourceUpdateViewTests,
    ResourceDeleteViewTests,
)
from resources.tests.test_admin_views import (
    AdminResourceAccessControlTests,
    AdminResourceListViewTests,
    AdminResourceCreateViewTests,
    AdminResourceUpdateViewTests,
    AdminResourceDeleteViewTests,
    AdminEducationLevelCRUDTests,
    AdminGradeCRUDTests,
    AdminLearningAreaCRUDTests,
)

__all__ = [
    # Models
    "EducationLevelModelTests",
    "GradeModelTests",
    "LearningAreaModelTests",
    "ResourceItemModelTests",
    # Forms
    "ResourceItemFormTests",
    # Cache
    "GetLearningAreasTests",
    "GetGradesTests",
    "GetEducationLevelsTests",
    "GetResourceTypesTests",
    "GetSlugBasedObjectTests",
    "GetAcademicSessionsTests",
    # Signals
    "LearningAreaSignalTests",
    "GradeSignalTests",
    "EducationLevelSignalTests",
    # Utils
    "GetYearAndMonthTests",
    "FileUploadPathTests",
    "PublicFilesStorageCallableTests",
    # Public Views
    "ResourceListViewTests",
    "ResourceDetailViewTests",
    "IncrementDownloadsViewTests",
    "ToggleFavoriteViewTests",
    "ResourceTypeDetailViewTests",
    "EducationLevelDetailsViewTests",
    "LearningAreaDetailsViewTests",
    "GradeDetailsViewTests",
    "AcademicSessionDetailViewTests",
    "LearningAreaListViewTests",
    "GradeListViewTests",
    "AcademicSessionListViewTests",
    "ResourceCreateViewTests",
    "ResourceUpdateViewTests",
    "ResourceDeleteViewTests",
    # Admin Views
    "AdminResourceAccessControlTests",
    "AdminResourceListViewTests",
    "AdminResourceCreateViewTests",
    "AdminResourceUpdateViewTests",
    "AdminResourceDeleteViewTests",
    "AdminEducationLevelCRUDTests",
    "AdminGradeCRUDTests",
    "AdminLearningAreaCRUDTests",
]
