from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from portals.decorators import role_required
from .forms import ClassArmForm
from profiles.models import TeacherProfile
from .models import Class, ClassArm, Subject
from users.models import User

# Create your views here.
@login_required
@role_required('ADMIN')
def create_class_arm(request):
    level_id = request.GET.get('level_id') or request.POST.get('level_id')
    level = get_object_or_404(Class, id=level_id, school=request.user.school)

    if request.method == 'POST':
        form = ClassArmForm(request.POST)
        if form.is_valid():
            arm = form.save(commit=False)
            arm.school = request.user.school
            arm.class_level = level
            arm.save()

            if arm.class_teacher:
                teacher_profile = get_object_or_404(TeacherProfile, user=arm.class_teacher, school=request.user.school)
                teacher_profile.class_arms.add(arm)
            total_count = ClassArm.objects.filter(school=request.user.school).count()

            return render(request, 'academics/partials/arm_row.html', {
                'arm': arm,
                'level': arm.class_level,
                'total_arms': total_count,
                
            })
        else:
            print(form.errors)
   

@login_required
@role_required('ADMIN')
def load_arms(request, level_id):
    level = get_object_or_404(Class, id=level_id, school=request.user.school)
    
    arms = ClassArm.objects.filter(
        class_level=level, 
        school=request.user.school
    ).select_related('class_teacher')
    teachers = User.objects.filter(role='TEACHER', school=request.user.school)

    
    return render(request, 'academics/partials/arms_stage.html', {
        'level': level,
        'arms': arms,
        'arm_count': arms.count(),
        'teachers': teachers
    })

@login_required
@role_required('ADMIN')
def manage_arms(request):
    school = request.user.school

    levels = Class.objects.filter(school=school).order_by('order')
    total_arms = ClassArm.objects.filter(school=school).count()
    context = {
        'levels': levels,
        'total_arms': total_arms
    }

    return render(request, 'academics/manage-arms.html', context)

@login_required
@role_required('ADMIN')
def delete_arm_htmx(request, arm_id):
    arm = get_object_or_404(ClassArm, id=arm_id, school=request.user.school)
    arm.delete()
    return HttpResponse('')

@login_required
@role_required('ADMIN')
def manage_subjects(request):
    categories = ['All', 'Junior', 'Science', 'Commercial', 'Arts', 'Trade']

    return render(request, 'academics/manage-subs.html', {'categories': categories})


@login_required
@role_required('ADMIN')
def load_sub(request, category):
    filters = {
        'Junior': ['JNR_CORE', 'JUNIOR'],
        'Science': ['SNR_CORE', 'SCIENCE', 'VOCATIONAL_TRADE'],
        'Commercial': ['SNR_CORE', 'COMMERCIAL', 'VOCATIONAL_TRADE'],
        'Arts': ['SNR_CORE', 'ARTS_HUMANITIES', 'VOCATIONAL_TRADE'],
    }
    
    target_categories = filters.get(category)
    
    if target_categories:
        subjects = Subject.objects.filter(category__in=target_categories).order_by('name')
    else:
        subjects = Subject.objects.all().order_by('category', 'name')

    return render(request, 'academics/partials/subs_stage.html', {
        'subjects': subjects,
        'category_name': category 
    })
