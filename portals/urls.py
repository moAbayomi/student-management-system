from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home, name="portal_home"),
    path("admin-portal/", views.admin_dashboard, name="admin"),
    path("admin-portal/students", views.students_directory, name="manage-students"),
    path(
        "admin-portal/students/details/<int:id>",
        views.student_detail,
        name="student-detail",
    ),
    path("admin-portal/students/create", views.create_student, name="create-student"),
    path(
        "admin-portal/students/details/edit/<int:id>",
        views.edit_student,
        name="edit-student",
    ),
    path("admin-portal/teachers", views.teachers_directory, name="manage-teachers"),
    path(
        "admin-portal/teachers/details/<int:id>",
        views.teacher_detail,
        name="teacher-detail",
    ),
    path("admin-portal/teachers/create", views.create_teacher, name="create-teacher"),
    path(
        "admin-portal/teachers/details/edit/<int:id>/",
        views.edit_teacher,
        name="edit-teacher",
    ),
    path(
        "admin-portal/teacher/assign-subject-assignment/",
        views.assign_teacher_subject,
        name="assign-subject-assignment",
    ),
    path(
        "admin-portal/teachers/create/load-subjects",
        views.load_subjects,
        name="load-subjects",
    ),
    path("admin-portal/class-console", views.class_console, name="class-console"),
    path(
        "admin-portal/class-console/class-details/<int:class_id>/",
        views.class_details,
        name="class-details",
    ),
    path(
        "admin-portal/class-console/arm-details/<int:arm_id>/",
        views.arm_details,
        name="classarm-details",
    ),
    path(
        "admin-portal/class-console/add-arm/<int:level_id>/",
        views.add_arm,
        name="add-arm",
    ),
    path(
        "admin-portal/teachers/load-arms", views.load_arms, name="load-arms-for-class"
    ),
    path(
        "admin-portal/class-console/load-core-subjects/<int:arm_id>/",
        views.load_core_subjects,
        name="load-core-subjects",
    ),
    path(
        "admin-portal/class-console/delete-arm/<int:arm_id>/",
        views.delete_arm,
        name="arm-delete",
    ),
    path(
        "admin-portal/class-console/manage-core-subjects/<int:class_id>/",
        views.manage_arm_core_subjects,
        name="manage-arm-core-subjects",
    ),
    path(
        "admin-portal/class-console/assign-teacher/<int:arm_id>/",
        views.assign_arm_class_teacher,
        name="assign-class-teacher",
    ),
    path(
        "admin-portal/class-console/remove-class-teacher/<int:arm_id>/",
        views.remove_arm_class_teacher,
        name="remove-class-teacher",
    ),
    path("admin/attendance", views.admin_attendance, name="admin-attendance"),
    path("admin/results", views.admin_result_view, name="admin-result-view"),
    path(
        "admin/announcements", views.admin_annoucements_view, name="admin-announcements"
    ),
    path("admin/fees", views.fees_view, name="admin-fees"),
    path("admin/settings", views.admin_settings_view, name="admin-settings"),
    path(
        "admin-portal/settings/school/", views.school_settings, name="school-settings"
    ),
    path("admin-portal/settings/sessions/", views.session_list, name="session-list"),
    path(
        "admin-portal/settings/sessions/create/",
        views.session_create,
        name="session-create",
    ),
    path(
        "admin-portal/settings/sessions/<int:session_id>/set-current/",
        views.session_set_current,
        name="session-set-current",
    ),
    path("teacher-portal/", views.teacher_dashboard, name="teacher"),
    path(
        "teacher-portal/my-students/", views.teachers_view_students, name="my-students"
    ),
    path(
        "teacher-portal/attendance/",
        views.attendance_teacher,
        name="class-teacher-attendance",
    ),
    path(
        "teacher-portal/attendance/date/<int:arm_id>/",
        views.arm_attendance_data,
        name="arm-attendance-data",
    ),
    path(
        "teacher-portal/attendance/date/save/<int:arm_id>/",
        views.save_attendance,
        name="save-attendance",
    ),
    path(
        "teacher-portal/subject_assignments/",
        views.subject_assignments_view,
        name="subject-assignments",
    ),
    path("teacher-portal/results/", views.results_view, name="results-view"),
    path("student-portal/", views.student_dashboard, name="student"),
    path(
        "admin-portal/settings/terms/<int:term_id>/edit/",
        views.term_edit,
        name="term-edit",
    ),
    path(
        "admin-portal/settings/grade-components/",
        views.grade_component_list,
        name="grade-components",
    ),
    path(
        "admin-portal/settings/terms/<int:term_id>/set-current/",
        views.term_set_current,
        name="term-set-current",
    ),
]
