"""
resources/models.py

CBE (Competency-Based Education) content models.

Hierarchy:
    EducationLevel → Grade → ResourceItem
                 LearningArea ↗

Future-proofed for multivendor marketplace with vendor FK, pricing,
and download tracking fields.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class EducationLevel(models.Model):
    """
    Top-level curriculum classification.

    Examples: Pre-Primary, Lower Primary, Upper Primary,
              Junior Secondary, Senior Secondary.
    """

    name: str = models.CharField(max_length=100, unique=True)
    slug: str = models.SlugField(max_length=100, unique=True, db_index=True)
    order: int = models.PositiveIntegerField(
        default=0,
        help_text="Display order in selects and navigation.",
    )

    class Meta:
        verbose_name = "Education Level"
        verbose_name_plural = "Education Levels"
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Grade(models.Model):
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

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        ordering = ["level__order", "order", "name"]
        unique_together = [("level", "name")]

    def __str__(self) -> str:
        return f"{self.level.name} — {self.name}"


class LearningArea(models.Model):
    """
    A subject / learning area in the CBC curriculum.

    Examples: Mathematics, Creative Arts, English, Kiswahili,
              Integrated Science, Social Studies.
    """

    name: str = models.CharField(max_length=100, unique=True)
    slug: str = models.SlugField(max_length=100, unique=True, db_index=True)

    class Meta:
        verbose_name = "Learning Area"
        verbose_name_plural = "Learning Areas"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ResourceItem(models.Model):
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
        max_length=255,
        db_index=True,
    )
    description: str = models.TextField()

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

    # --- File Storage (Cloudflare R2 in production) ---
    file = models.FileField(
        upload_to="resources/%Y/%m/",
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
    resource_type : str = models.CharField(
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
            ("report_card", "Report Card")
        ],
        default="other",
        help_text="The type of resource.",
    )
        
    downloads: int = models.PositiveIntegerField(
        default=0,
        help_text="Cumulative download count.",
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resource Item"
        verbose_name_plural = "Resource Items"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["grade", "learning_area"]),
            models.Index(fields=["is_free", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        from django.urls import reverse
        return reverse("resources:resource_detail", kwargs={"slug": self.slug})

    def increment_downloads(self) -> None:
        """
        Atomically increment the download counter.
        Use F() to avoid race conditions under concurrent requests.
        """
        from django.db.models import F
        ResourceItem.objects.filter(pk=self.pk).update(downloads=F("downloads") + 1)
        self.refresh_from_db(fields=["downloads"])
