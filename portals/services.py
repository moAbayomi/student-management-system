from academics.services import AcademicsManagementService
from schools.services import SchoolManagementService
from users.services import UserManagegementService
from profiles.services import StudentProfileService, TeacherProfileService
from django.core.paginator import Paginator
from datetime import datetime


class AdminOverviewAggregator:
    @staticmethod
    def get_complete_overview():
        profile_stats = StudentProfileService.get_stats()
        user_stats = UserManagegementService.get_stats()
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

        paginator = Paginator(student_qs, 20)
        page_obj = paginator.get_page(page_no)


        class_stats = AcademicsManagementService.get_stats()
        date = datetime.now().date().strftime('%A, ''%d' ' %B' ' %Y')


        return {
            'students': page_obj,
            **students_stats,
            **class_stats,
            'date': date
        }
    
class AdminTeacherOverviewAggregator:
    @staticmethod
    def get_teachers_overview(page_no=1):
        teacher_qs = TeacherProfileService.get_teachers_queryset()
        teachers_stats = TeacherProfileService.get_stats()
        paginator = Paginator(teacher_qs, 5)
        page_obj = paginator.get_page(page_no)

        return {
            'teachers': page_obj,
            **teachers_stats
        }
    

    
    