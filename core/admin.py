from django.contrib import admin

from core.models import Term, Year, AcademicSession

admin.site.register(Term)
admin.site.register(Year)
admin.site.register(AcademicSession)
