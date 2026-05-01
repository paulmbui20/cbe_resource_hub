"""
resources/models.py

CBE (Competency-Based Education) content models.

Hierarchy:
    EducationLevel → Grade → ResourceItem
                 LearningArea ↗

Future-proofed for multivendor marketplace with vendor FK, pricing,
and download tracking fields.
"""

from validators import DeepSignatureValidator

from django.conf import settings
from django.db import models
from django.db.models import F
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import slugify
from tinymce.models import HTMLField

from core.models import AcademicSession
from resources.utils import PublicFilesStorageCallable, file_upload_path
from seo.models import SEOModel, SlugRedirectMixin


class EducationLevel(SEOModel, SlugRedirectMixin, models.Model):
    """
    Top-level curriculum classification.

    Examples: Pre-Primary, Lower Primary, Upper Primary,
              Junior Secondary, Senior Secondary.
    """

    name: str = models.CharField(max_length=100)
    slug: str = models.SlugField(max_length=110, unique=True, db_index=True)
    order: int = models.PositiveIntegerField(
        default=0,
        help_text="Display order in selects and navigation.",
    )

    class Meta:
        verbose_name = "Education Level"
        verbose_name_plural = "Education Levels"
        ordering = ["order", "slug"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_education_level_name",
                violation_error_message="Education level name must be unique",
            )
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)[:110]
        if self.name and not self.meta_title:
            self.meta_title = self.name
        super().save(*args, **kwargs)


class GradeManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "level",
            )
        )


class Grade(SEOModel, SlugRedirectMixin, models.Model):
    """
    A specific grade/class within an EducationLevel.

    Examples: Grade 1, Grade 4, Form 1, PP1, PP2.
    """

    level: EducationLevel = models.ForeignKey(
        EducationLevel,
        on_delete=models.PROTECT,
        related_name="grades",
    )
    name: str = models.CharField(max_length=50)
    order: int = models.PositiveIntegerField(default=0)
    slug: str = models.SlugField(max_length=60, unique=True, db_index=True)

    objects = GradeManager()

    def get_absolute_url(self) -> str:
        return reverse("resources:grade_details", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if self.name and not self.slug:
            self.slug = slugify(self.name)[:60]
        if self.name and not self.meta_title:
            self.meta_title = self.name

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        ordering = ["level__order", "order", "name"]
        unique_together = [("level", "slug")]

    def __str__(self) -> str:
        return f"{self.level.name} — {self.name}"


class LearningArea(SEOModel, SlugRedirectMixin, models.Model):
    """
    A subject / learning area in the CBC curriculum.

    Examples: Mathematics, Creative Arts, English, Kiswahili,
              Integrated Science, Social Studies.
    """

    name: str = models.CharField(max_length=100)
    slug: str = models.SlugField(max_length=110, unique=True, db_index=True)

    def get_absolute_url(self) -> str:
        return reverse("resources:learning_area_details", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = "Learning Area"
        verbose_name_plural = "Learning Areas"
        ordering = ["slug"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)[:110]
        if self.name and not self.meta_title:
            self.meta_title = self.name
        super().save(*args, **kwargs)


class ResourcesPublicFilesStorageCallable(PublicFilesStorageCallable):
    def deconstruct(self):
        """
        Allow Django to serialize this for migrations.
        """
        return ("resources.models.ResourcesPublicFilesStorageCallable", [], {})


class ResourceItemManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "grade",
                "grade__level",
                "vendor",
                "learning_area",
                "academic_session",
                "academic_session__current_year",
                "academic_session__current_term",
            )
            .prefetch_related("favorited_by")
        )


class ResourceItem(SEOModel, SlugRedirectMixin, models.Model):
    """
    The core document model — a downloadable educational resource.

    File uploads are stored via `DEFAULT_FILE_STORAGE` which is configured
    to use Cloudflare R2 in production (via django-storages + boto3).

    Multivendor marketplace fields (vendor, is_free, price, downloads) are
    included now for zero-migration cost when the marketplace is activated.
    """

    title: str = models.CharField(max_length=255)
    slug: str = models.SlugField(
        unique=True,
        max_length=265,
        db_index=True,
    )
    description: str = HTMLField(default="", blank=True)

    # --- Curriculum Classification ---
    grade: Grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name="resources",
    )
    learning_area: LearningArea = models.ForeignKey(
        LearningArea,
        on_delete=models.PROTECT,
        related_name="resources",
    )
    academic_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        related_name="resources",
        null=True,
        blank=True,
    )

    # --- File Storage (Cloudflare R2 in production) ---
    file = models.FileField(
        upload_to=file_upload_path,
        storage=ResourcesPublicFilesStorageCallable(),
        max_length=300,
        validators=[
            DeepSignatureValidator(
                allowed_mimetypes={
                    # Currently Accepted:
                    # Office Open XML (modern Microsoft Office)
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    # OpenDocument Format (LibreOffice / OpenOffice / Google Docs export)
                    "application/vnd.oasis.opendocument.text",
                    "application/vnd.oasis.opendocument.spreadsheet",
                    "application/vnd.oasis.opendocument.presentation",
                    # Legacy Microsoft Office (OLE2 compound document)
                    "application/msword",
                    "application/vnd.ms-excel",
                    "application/vnd.ms-powerpoint",
                    # Other
                    "application/rtf",
                    "application/epub+zip",
                    "application/pdf",
                }
            )
        ],
    )

    # --- Multivendor Marketplace Future-Proofing ---
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources",
        help_text="The content creator / vendor who owns this resource.",
    )
    is_free: bool = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Free resources are downloadable without payment.",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default="0.00",
        help_text="Purchase price in KES. Ignored when is_free=True.",
    )
    resource_type: str = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ("lesson_plan", "Lesson Plan"),
            ("schemes_of_work", "Schemes of Work"),
            ("curriculum_design", "Curriculum Design"),
            ("record_of_work", "Record of Work"),
            ("teachers_guide", "Teachers Guide"),
            ("textbook", "Textbook"),
            ("notes", "Notes"),
            ("exam", "Exam"),
            ("other", "Other"),
            ("report_card", "Report Card"),
            ("holiday_assignment", "Holiday Assignment"),
            ("setbook_guide", "Set Book Guide"),
        ],
        default="other",
        help_text="The type of resource.",
    )

    downloads: int = models.PositiveIntegerField(
        default=0,
        help_text="Cumulative download count.",
    )

    objects = ResourceItemManager()

    class Meta:
        verbose_name = "Resource Item"
        verbose_name_plural = "Resource Items"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["grade", "learning_area"]),
            models.Index(fields=["is_free", "-created_at"]),
            models.Index(fields=["-updated_at"]),
            models.Index(fields=["-resource_type"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if self.title:
            self.slug = slugify(self.title[:265])
            self.meta_title = self.title[:60]
        if self.description and not self.meta_description:
            self.meta_description = strip_tags(self.description)[:160]
        if self.is_free:
            self.price = 0.00
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.file:
            self.file.delete(save=False)
        return super().delete(using=using, keep_parents=keep_parents)

    def get_absolute_url(self) -> str:
        return reverse("resources:resource_detail", kwargs={"slug": self.slug})

    def increment_downloads(self) -> None:
        """
        Atomically increment the download counter.
        Use F() to avoid race conditions under concurrent requests.
        """
        ResourceItem.objects.filter(pk=self.pk).update(downloads=F("downloads") + 1)
        self.refresh_from_db(fields=["downloads"])
