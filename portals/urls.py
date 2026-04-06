from django.urls import path
from .views import home, admin_dashboard, teacher_dashboard, student_dashboard, man_students, man_teachers, add_student, add_teacher, deactivate_teacher

app_name = 'portal'

urlpatterns = [
    path('', home, name='portal_home'),
    path('admin/', admin_dashboard, name='admin'),
    path('admin/teachers', man_teachers, name='man-teachers'),
    path('admin/teachers/add', add_teacher, name='add-teacher'),
    path('admin/teachers/<int:teacher_id>/deactivate/', deactivate_teacher, name='deactivate-teacher'),
    path('teacher/', teacher_dashboard, name='teacher'),
    path('teacher/students/', man_students, name='man-students'),
    path('teacher/student/add', add_student, name='add-student'),
    path('student/', student_dashboard, name='student'),
]