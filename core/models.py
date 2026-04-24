from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.utils import current_year
from seo.mixins import SlugRedirectMixin


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Term(TimeStampedModel, models.Model):
    term_number = models.PositiveSmallIntegerField(
        help_text="e.g., 1 for Term 1", unique=True
    )

    def __str__(self):
        return f"Term {self.term_number}"

    class Meta:
        ordering = ['-term_number']


class Year(models.Model):
    year = models.PositiveSmallIntegerField(
        default=current_year, unique=True,
        help_text="e.g., 2026"
    )

    def __str__(self):
        return f"{self.year}"

    class Meta:
        ordering = ['-year']


class AcademicSessionManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset().select_related(
                "current_year", "current_term"
            ).prefetch_related("resources", )
        )


class AcademicSession(SlugRedirectMixin, models.Model):
    current_year = models.ForeignKey(Year, on_delete=models.CASCADE, related_name='sessions')
    current_term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='sessions')
    slug = models.SlugField(max_length=255, unique=True, db_index=True, default='', blank=True)

    objects = AcademicSessionManager()

    class Meta:
        verbose_name = "Academic Session"
        verbose_name_plural = "Academic Sessions"
        unique_together = ('current_year', 'current_term')
        ordering = ["current_year", "current_term"]

    def __str__(self):
        return f"{self.current_year} - {self.current_term}"

    def get_absolute_url(self) -> str:
        return reverse("resources:academic_session_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if self.slug == '' or not self.slug and (self.current_year and self.current_term):
            self.slug = slugify(f"{self.current_year}-{self.current_term}"[:255])
        super().save(*args, **kwargs)
