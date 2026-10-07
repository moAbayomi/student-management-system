from .models import User

class UserManagementService:
    @staticmethod
    def get_stats():
        teacher_users = User.objects.filter(role='TEACHER')
        student_users = User.objects.filter(role='STUDENT')
        return {
            'teacher_users': teacher_users,
            'student_users': student_users,
            'total_teachers_users': teacher_users.count(),
            'total_students_users': student_users.count(),
            
        }