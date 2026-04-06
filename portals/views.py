from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from academics.models import ClassArm
from profiles.models import TeacherProfile, StudentProfile
from users.models import User
from .forms import TeacherCreationForm, StudentCreationForm ,generate_temp_password


@login_required
def home(request):
    """ The single 'Entry Point' for the e-portal """
    user = request.user

    
    role = getattr(user, 'role', None)
    
    if role == 'ADMIN':
        return redirect('portal:admin')
    
    elif role == 'TEACHER':
        return redirect('portal:teacher')
    
    elif role == 'STUDENT':
        return redirect('portal:student')
    
    else:
        return redirect('public:home')
            

@login_required
@role_required('ADMIN')
def admin_dashboard(request):
    
    return render(request, 'portals/admin_dashboard.html')

@login_required
@role_required('TEACHER')
def teacher_dashboard(request):
    teacher = get_object_or_404(TeacherProfile, user=request.user)
    subjects = teacher.subjects.all()
    arms = teacher.class_arms.all()
    arm_count = arms.count()
    subject_count = subjects.count()

    
    return render(request, 'portals/teacher_dashboard.html', {
        'teacher': teacher,
        'class_arms': arms,
        'arm_count': arm_count,
        'subjects': subjects,
        'subject_count': subject_count
        })

@login_required
@role_required('STUDENT')
def student_dashboard(request):
    
    return render(request, 'portals/student_dashboard.html')


@login_required
@role_required('TEACHER', 'ADMIN')
def man_students(request):
    user = request.user
    class_arm = ClassArm.objects.get(class_teacher=user)
    students = get_list_or_404(StudentProfile, class_arm=class_arm)
    return render(request, 'portals/manage_students.html', {'students': students})

@login_required
@role_required('TEACHER', 'ADMIN')
def add_student(request):
    school = request.user.school
    teacher = request.user
    try:
        teacher_arm = ClassArm.objects.get(class_teacher=teacher)
    except ClassArm.DoesNotExist:
        # If the teacher isn't assigned to a class, they shouldn't be onboarding students
        messages.error(request, "Access Denied: You are not assigned as a Class Teacher.")
        return redirect('portal:man-students')

    if request.method == 'POST':
        form = StudentCreationForm(data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                temp_password = generate_temp_password()
                user = User.objects.create(
                    username=form.cleaned_data['username'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data.get('email', ''),
                    role='STUDENT',
                    school=school,    
                )
                user.set_password(temp_password)
                user.save()

                
                std_profile = StudentProfile.objects.create(
                    user=user,
                    school=school,
                    admission_number=None,
                    date_of_birth=form.cleaned_data['date_of_birth'],
                    class_arm=teacher_arm
                )

                arm_subjects = teacher_arm.subjects.all()
                std_profile.subjects.set(arm_subjects)
            print('success!! -> student is created!')
            return render(request, 'portals/partials/student_created.html', {
                'student': user,
                'temp_password': temp_password,
            })
    else:
        form = StudentCreationForm()

    return render(request, 'portals/add_student.html', {'form': form, 'teacher_arm': teacher_arm})


@login_required
@role_required('ADMIN')
def man_teachers(request):
    school = request.user.school
    teachers = TeacherProfile.objects.filter(
        school=school
    ).select_related('user').prefetch_related('subjects', 'class_arms')

    return render(request, 'portals/manage_staff.html', {
        'teachers': teachers,
    })


@login_required
@role_required('ADMIN')
def add_teacher(request):
    school = request.user.school

    if request.method == 'POST':
        form = TeacherCreationForm(school=school, data=request.POST)
        if form.is_valid():
            temp_password = generate_temp_password()

            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data.get('email', ''),
                password=temp_password,
                role='TEACHER',
                school=school,
            )

            profile = TeacherProfile.objects.create(
                user=user,
                school=school,
                employee_id=form.cleaned_data.get('employee_id') or None,
            )
            profile.subjects.set(form.cleaned_data['subjects'])
            profile.class_arms.set(form.cleaned_data['class_arms'])

            return render(request, 'portals/partials/teacher_created.html', {
                'teacher': user,
                'temp_password': temp_password,
            })
    else:
        form = TeacherCreationForm(school=school)

    return render(request, 'portals/add_teacher.html', {'form': form})


@login_required
@role_required('ADMIN')
def deactivate_teacher(request, teacher_id):
    school = request.user.school
    profile = get_object_or_404(TeacherProfile, id=teacher_id, school=school)
    profile.user.is_active = False
    profile.user.save()
    return render(request, 'portals/partials/teacher_row.html', {
        'teacher': profile,
    })