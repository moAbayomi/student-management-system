from .models import ActivityLog, AcademicSession, AcademicTerm, School


def get_school():
    """Return the one School record, or None if it hasn't been set up yet."""
    return School.objects.first()


def get_current_session():
    """Return the current AcademicSession, or None if none is marked current."""
    return AcademicSession.objects.filter(is_current=True).first()


def get_current_term():
    """Return the current AcademicTerm, or None if none is marked current."""
    return AcademicTerm.objects.select_related('session').filter(is_current=True).first()


class SchoolManagementService:
    @staticmethod
    def get_stats():
        curr_term = get_current_term()
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