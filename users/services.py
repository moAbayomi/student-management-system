from .models import User

class UserManagegementService:
    @staticmethod
    def get_stats():
        teachers = User.objects.filter(role='TEACHER')
        students = User.objects.filter(role='STUDENT')
        return {
            'teachers': teachers,
            'students': students,
            'total_teachers': teachers.count(),
            'total_students': students.count(),
            
        }