from academics.services import AcademicsManagementService
from schools.services import SchoolManagementService
from profiles.models import TeacherProfile, StudentProfile
from academics.models import SubjectAssignment, DailyAttendance
from users.services import UserManagementService
from profiles.services import StudentProfileService, TeacherProfileService
from django.core.paginator import Paginator
from datetime import datetime
from django.db.models import Q
import json


class AdminOverviewAggregator:
    @staticmethod
    def get_complete_overview():
        profile_stats = StudentProfileService.get_stats()
        user_stats = UserManagementService.get_stats()
        school_stats = SchoolManagementService.get_stats()
        academic_stats = AcademicsManagementService.get_stats()
        date = datetime.now().date().strftime('%A, ''%d' ' %B' ' %Y')


        return {
            **profile_stats,
            **user_stats,
            **school_stats,
            **academic_stats,
            'date': date
        }

class AdminStudentOverviewAggregator:
    @staticmethod
    def get_student_overview(page_no=1):
        student_qs = StudentProfileService.get_students_queryset()
        students_stats = StudentProfileService.get_stats()
        user_stats = UserManagementService.get_stats()


        paginator = Paginator(student_qs, 20)
        page_obj = paginator.get_page(page_no)


        class_stats = AcademicsManagementService.get_stats()
        date = datetime.now().date().strftime('%A, ''%d' ' %B' ' %Y')


        return {
            'students': page_obj,
            **students_stats,
            **class_stats,
            **user_stats,
            'date': date
        }
    
class AdminTeacherOverviewAggregator:
    @staticmethod
    def get_teachers_overview(page_no=1):
        teacher_qs = TeacherProfileService.get_teachers_queryset()
        user_stats = UserManagementService.get_stats()
        teachers_stats = TeacherProfileService.get_stats()
        paginator = Paginator(teacher_qs, 5)
        page_obj = paginator.get_page(page_no)

        return {
            'teachers': page_obj,
            **teachers_stats,
            **user_stats
        }
    
class AdminClassConsoleOverviewAggregator:
    @staticmethod
    def get_class_console_overview():
        class_stats = AcademicsManagementService.get_stats()

        return {
            **class_stats
        }

    
    
class TeacherOverviewAggregator:
    @staticmethod
    def get_complete_overview(user):
        teacher = TeacherProfile.objects.get(user=user)
        class_arm = teacher.class_teacher_of.first()
        arm_count = teacher.class_teacher_of.count()
        students = StudentProfile.objects.none() if not class_arm else StudentProfile.objects.filter(class_arm=class_arm)
        total_student_count = students.count()
        subject_assignments = SubjectAssignment.objects.filter(teacher=teacher).select_related('class_arm', 'subject', 'session')
        subject_assignment_count = subject_assignments.count()
        my_date = datetime.now().date().strftime("%A, %-d, %B %Y").lower()

        return {
            'teacher': teacher,
            'class_arm': class_arm,
            'arm_count': arm_count,
            'students': students,
            'total_student_count': total_student_count,
            'subject_assignments': subject_assignments,
            'subject_assignment_count': subject_assignment_count,
            'date': my_date
        }
    
    @staticmethod
    def get_paginated_students(user, page_no=1, search_query=None):
        teacher = TeacherProfile.objects.get(user=user)
        class_arm = teacher.class_teacher_of.first()
        total_arms = teacher.class_teacher_of.all().count()
        students = StudentProfile.objects.none() if not class_arm else StudentProfile.objects.filter(class_arm=class_arm).select_related('user')
        real_total_students = StudentProfile.objects.none().count() if not class_arm else StudentProfile.objects.filter(class_arm=class_arm).count()

        if search_query:
            students = students.filter(Q(user__first_name__icontains=search_query) | Q(user__last_name__icontains=search_query))
        
        paginator = Paginator(students, 20)
        page_obj = paginator.get_page(page_no)
        if search_query:
            return {
                'students': page_obj,
                'total_students': paginator.count
            }
        else:
            return {
                'students': page_obj,
                'total_arms': total_arms,
                'real_total_students': real_total_students,
                'total_students': paginator.count
            }


class TeacherAttendanceOverviewAggregator:
    @staticmethod
    def get_attendance_overview(user):
        teacher = TeacherProfile.objects.get(user=user)
        class_arm = teacher.class_teacher_of.first()
        date = datetime.now().date()
        attendance_data = DailyAttendance.objects.filter(date=date, class_arm=class_arm)
        students = StudentProfile.objects.none() if not class_arm else StudentProfile.objects.filter(class_arm=class_arm).select_related('user')
        total_students = students.count()
        status_map = {}
        for std in students:
            status_map[std.id] = 'P'

        existing_status = {data.id: data.status for data in attendance_data}
        status_map.update(existing_status)
        students_data = []

        for s in students:
            students_data.append({
                'id': s.id,
                'name': s.user.get_full_name(),
                'admission': s.admission_number or '',
                'initials': s.user.first_name[0].upper() + s.user.last_name[0].upper(),
                'status': status_map.get(str(s.id), 'P'),
                'remark': ''
            })


        return {
            'teacher': teacher,
            'class_arm': class_arm,
            'date': date,
            'students_data_json': students_data,
            'total_students': total_students
        }


class TeacherSubjectAssignmentOverViewAggregator:
    @staticmethod
    def get_subject_assignments_overview(user):
        teacher = TeacherProfile.objects.get(user=user)
        subject_assignments = teacher.assignments.all()

        return {
            'teacher': teacher,
            'subject_assignments': subject_assignments
        }