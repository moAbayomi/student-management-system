from django.contrib import admin
from .models import School, AcademicSession, AcademicTerm
# Register your models here.
admin.site.register(School)
admin.site.register(AcademicSession)
admin.site.register(AcademicTerm)