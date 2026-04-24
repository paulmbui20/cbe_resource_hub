from django.db import models

from core.utils import current_year


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


class Year(models.Model):
    year = models.PositiveSmallIntegerField(default=current_year, unique=True)

    def __str__(self):
        return f"{self.year}"

    class Meta:
        ordering = ['-year']


class AcademicSession(models.Model):
    current_year = models.ForeignKey(Year, on_delete=models.CASCADE, related_name='sessions')
    current_term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='sessions')

    class Meta:
        verbose_name = "Academic Session"
        verbose_name_plural = "Academic Sessions"
        unique_together = ('current_year', 'current_term')

    def __str__(self):
        return f"{self.current_year} - {self.current_term}"
