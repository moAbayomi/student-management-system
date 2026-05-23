from django.urls import path
from .views import home, admin_dashboard, teacher_dashboard, student_dashboard, students_directory, student_detail, teachers_directory, create_teacher,edit_teacher, load_subjects, class_console, admin_attendance, admin_result_view, admin_annoucements_view, fees_view, teacher_detail, create_student, edit_student, admin_settings_view

app_name = 'portal'

urlpatterns = [
    path('', home, name='portal_home'),
    path('admin-portal/', admin_dashboard, name='admin'),
    path('admin-portal/students', students_directory, name='manage-students'),
    path('admin-portal/students/details/<int:id>', student_detail, name='student-detail'),
    path('admin-portal/students/create', create_student, name='create-student'),
    path('admin-portal/students/details/edit/<int:id>', edit_student, name='edit-student'),
    path('admin-portal/teachers', teachers_directory, name='manage-teachers'),
    path('admin-portal/teachers/details/<int:id>', teacher_detail, name='teacher-detail'),
    path('admin-portal/teachers/create', create_teacher, name='create-teacher'),
    path('admin-portal/teachers/details/edit/<int:id>', edit_teacher, name='edit-teacher'),
    path('admin-portal/teachers/create/load-subjects', load_subjects, name='load-subjects'),
    path('admin/class-console', class_console, name='class-console'),
    path('admin/attendance', admin_attendance, name='admin-attendance'),
    path('admin/results', admin_result_view, name='admin-result-view'),
    path('admin/announcements', admin_annoucements_view, name='admin-announcements'),
    path('admin/fees', fees_view, name='admin-fees'),
    path('admin/settings', admin_settings_view, name='admin-settings'),
    path('teacher/', teacher_dashboard, name='teacher'),
   
]