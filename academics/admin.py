from django.contrib import admin
from .models import Class, ClassArm, Subject, SubjectAssignment, Result, DailyAttendance

# Register your models here.
admin.site.register(Class)
admin.site.register(ClassArm)
admin.site.register(Subject)
admin.site.register(Result)
admin.site.register(SubjectAssignment)
admin.site.register(DailyAttendance)



