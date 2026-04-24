from django.contrib import admin

from core.models import Term, Year, AcademicSession


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    pass


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    pass


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ("current_term", "current_year")
    list_filter = ("current_term", "current_year")
