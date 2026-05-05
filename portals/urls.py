from django.urls import path
from .views import home, admin_dashboard, teacher_dashboard, student_dashboard, man_students, man_teachers, add_student, add_teacher, deactivate_teacher, man_subjects, show_subjects, view_student, view_teacher, man_all_students, search_student, edit_subjects_taken, change_classteacher, edit_teacher_details, bulk_grading_view, class_broadsheet_view, view_result, man_attendance, attendance_overview, test_plotly

app_name = 'portal'

urlpatterns = [
    path('', home, name='portal_home'),
    path('admin/', admin_dashboard, name='admin'),
    path('admin/teachers', man_teachers, name='man-teachers'),
    path('admin/teachers/add', add_teacher, name='add-teacher'),
    path('admin/teachers/<int:teacher_id>/deactivate/', deactivate_teacher, name='deactivate-teacher'),
    path('teacher/', teacher_dashboard, name='teacher'),
    path('teacher/<int:id>/', view_teacher, name='view-teacher'),
    path('teacher/students/', man_students, name='man-students'),
    path('admin/students', man_all_students, name='all-students'),
    path('teacher/student/add', add_student, name='add-student'),
    path('student/', student_dashboard, name='student'),
    path('student/<int:id>/', view_student, name='view-student'),
    path('student/subjects', man_subjects, name='man-subjects'),
    path('student/subjects/show', show_subjects, name='show-subjects'),
    path('search_student/', search_student, name='search'),
    path('edit-subjects/<int:id>', edit_subjects_taken, name='edit-subjects'),
    path('edit-teacher/<int:id>/', edit_teacher_details, name='edit-teacher'),
    path('grading/<int:id>', bulk_grading_view, name='grading'),
    path('admin/change-teacher/<int:id>/', change_classteacher, name='change-classteacher'),
    path('teacher/class-broadsheet/<int:id>/', class_broadsheet_view, name='broadsheet'),
    path('student/result/<int:id>', view_result, name='result'),
    path('mark-attendance/<int:id>', man_attendance, name='save-attendance'),
    path('attendance-overview/<int:id>', attendance_overview, name='attendance-overview'),
    path('test/', test_plotly, name='test-plotly')
]