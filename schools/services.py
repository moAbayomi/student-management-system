from .models import ActivityLog
from .models import AcademicTerm


class SchoolManagementService:
    @staticmethod
    def get_stats():
        curr_term = AcademicTerm.objects.get(is_current=True)
        return {
            'curr_term': curr_term
        }
    

def log_activity(user, action, category="SYSTEM", description="", request=None):
    ip = None
    if request:
        # Helper to grab IP from request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

    return ActivityLog.objects.create(
        actor=user,
        action=action,
        category=category,
        description=description,
        ip_address=ip
    )