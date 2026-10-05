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
    level = get_object_or_404(Class, id=level_id)

    if request.method == 'POST':
        form = ClassArmForm(request.POST)
        if form.is_valid():
            arm = form.save(commit=False)
            arm.class_level = level
            arm.save()

            # Keep the teacher's profile in sync with the arm they now form-teach
            if arm.class_teacher:
                TeacherProfile.objects.filter(user=arm.class_teacher).update(assigned_class_arm=arm)
            total_count = ClassArm.objects.count()

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
    level = get_object_or_404(Class, id=level_id)
    
    
    arms = ClassArm.objects.filter(class_level=level).select_related('class_teacher')
    teachers = User.objects.filter(role='TEACHER')

    
    return render(request, 'academics/partials/arms_stage.html', {
        'level': level,
        'arms': arms,
        'arm_count': arms.count(),
        'teachers': teachers
    })

@login_required
@role_required('ADMIN')
def manage_arms(request):
    levels = Class.objects.all().order_by('order')
    total_arms = ClassArm.objects.count()
    context = {
        'levels': levels,
        'total_arms': total_arms
    }

    return render(request, 'academics/manage-arms.html', context)

@login_required
@role_required('ADMIN')
def delete_arm_htmx(request, arm_id):
    arm = get_object_or_404(ClassArm, id=arm_id)
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
