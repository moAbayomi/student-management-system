from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
def principal_dashboard(request):
    if request.user.role != "ADMIN":
        raise PermissionDenied  

    # Get only the staff belonging to THIS principal's school
    school = request.user.school
    staff_members = school.users.filter(role__in=["ADMIN", "TEACHER"])
    
    context = {
        'school': school,
        'staff_count': staff_members.count(),
        'staff_members': staff_members,
    }
    return render(request, 'portals/base.html', context)