from django.contrib import admin
from .models import School, AcademicSession, AcademicTerm, Announcement, ActivityLog


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    # Single-school setup: allow creating the school once, never deleting it.
    prepopulated_fields = {'slug': ('name',)}

    def has_add_permission(self, request):
        return not School.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class AcademicTermInline(admin.TabularInline):
    model = AcademicTerm
    extra = 0


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'is_current')
    inlines = [AcademicTermInline]


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_current', 'result_published', 'grading_deadline')
    list_filter = ('session',)


admin.site.register(Announcement)
admin.site.register(ActivityLog)
