from django.urls import path
from .views import home, admin_dashboard, teacher_dashboard, student_dashboard, man_students, man_teachers, add_student, add_teacher, deactivate_teacher, man_subjects, show_subjects, view_student, view_teacher, man_all_students, search_student

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
    path('/search_student', search_student, name='search')
]