from django.contrib import admin
from .models import StudentProfile, TeacherProfile, TeacherRole
# Register your models here.
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(TeacherRole)
