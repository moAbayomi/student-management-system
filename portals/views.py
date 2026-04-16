from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.db import transaction   
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from academics.models import ClassArm, Subject
from profiles.models import TeacherProfile, StudentProfile
from users.models import User
from .forms import TeacherCreationForm, StudentCreationForm, SubjectEnrollmentForm, ClassArmForm, generate_temp_password 


@login_required
def home(request):
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
    teacher_arm = ClassArm.objects.filter(class_teacher=request.user).first() 
    subjects = teacher.subjects.all()
    arms = teacher.class_arms.all() 
    arm_count = arms.count()
    subject_count = subjects.count()
    recent_students = StudentProfile.objects.filter(class_arm=teacher_arm).order_by('-id')[:3]

    
    return render(request, 'portals/teacher_dashboard.html', {
        'teacher': teacher,
        'class_arms': arms,
        'arm_count': arm_count,
        'subjects': subjects,
        'subject_count': subject_count,
        'recent_students': recent_students
        })

@login_required
@role_required('STUDENT')
def student_dashboard(request):
    from profiles.models import StudentProfile
    profile = StudentProfile.objects.select_related(
        'class_arm', 'class_arm__class_level', 'class_arm__class_teacher'
    ).get(user=request.user)

    return render(request, 'portals/student_dashboard.html', {
        'profile': profile,
    })

@login_required
@role_required('TEACHER', 'ADMIN')
def man_students(request):
    user = request.user
    if user.role == 'TEACHER':
        try:
            class_arm = ClassArm.objects.select_related('class_level').get(class_teacher=user)
            students = StudentProfile.objects.filter(class_arm=class_arm).select_related('user')
        except ClassArm.DoesNotExist:
            students = StudentProfile.objects.none()
        return render(request, 'portals/manage_students.html', 
        {
        'students': students,
        'base_template': 'portals/teacher_dashboard.html'
        })
    elif user.role == 'ADMIN':
        form = ClassArmForm(request.GET)
        students = StudentProfile.objects.select_related('users', 'class_arm', 'class_arm__class_level').all()

        if form.is_valid() and form.cleaned_data.get('class_arm'):
            selected_arm = form.cleaned_data.get('class_arm')
        selected_arm = request.GET.get('class_arm')
        students = StudentProfile.objects.select_related('user', 'class_arm', 'class_arm__class_level').filter(class_arm=selected_arm)

        context = {
            'students': students,
            'form': selected_arm,
            'base_template': 'portals/admin_dashboard.html'
        }

        return render(request, 'portals/manage_students.html', context)


@login_required
@role_required('TEACHER', 'ADMIN')
def add_student(request):
    school = request.user.school
    user_role = request.user.role
    teacher_arm = None
    
    
    if user_role == 'TEACHER':
        try:
            teacher_arm = ClassArm.objects.get(class_teacher=request.user)
        except ClassArm.DoesNotExist:
            # If the teacher isn't assigned to a class, they shouldn't be onboarding 
            messages.error(request, "Access Denied: You are not assigned as a Class Teacher.")
            return redirect('portal:man-students')

    if request.method == 'POST':
        form = StudentCreationForm(data=request.POST, user_role=user_role)
        selected_arm = teacher_arm if user_role == 'TEACHER' else form.cleaned_data.get('class_arm')
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

                is_junior = 'JSS' in selected_arm.class_level.name.upper()
                is_senior = 'SSS' in selected_arm.class_level.name.upper()

                
                arm_name = selected_arm.name.upper()
                stream = 'ARTS'

                if is_senior:
                    if arm_name == 'A':
                        stream = 'SCIENCE'
                    elif arm_name == 'B':
                        stream = 'COMMERCIAL'

                
                category_map = {
                    'JUNIOR': ['JNR_CORE', 'JUNIOR'],
                    'SCIENCE': ['SNR_CORE', 'SCIENCE', 'VOCATIONAL_TRADE'],
                    'COMMERCIAL': ['SNR_CORE', 'COMMERCIAL', 'VOCATIONAL_TRADE'],
                    'ARTS': ['SNR_CORE', 'ARTS_HUMANITIES', 'VOCATIONAL_TRADE'],
                }
                
                key= 'JUNIOR'if is_junior else stream

                target_categories = category_map[key]
                subjects = Subject.objects.filter(category__in=target_categories).order_by('name')
                std_profile = StudentProfile.objects.create(
                    user=user,
                    school=school,
                    admission_number=None,
                    date_of_birth=form.cleaned_data['date_of_birth'],
                    class_arm=selected_arm
                )
                std_profile.subjects.set(subjects)
            print('success!! -> student is created!')
            return render(request, 'portals/partials/student_created.html', {
                'student': user,
                'temp_password': temp_password,
            })
    else:
        form = StudentCreationForm(user_role=user_role)

        base_template = None
        if user_role == 'ADMIN':
            base_template = 'portals/admin_dashboard.html'
        if user_role == 'TEACHER':
            base_template = 'portals/teacher_dashboard.html'

    return render(request, 'portals/add_student.html', {'form': form, 'teacher_arm': teacher_arm, 'is_admin': user_role == 'ADMIN', 'base_template': base_template})


@login_required
@role_required('ADMIN')
def man_all_students(request):
    students = StudentProfile.objects.all()
    return render(request, 'portals/all_students.html', {'students': students})

@login_required
@role_required('ADMIN')
def search_student(request):
    name = request.POST.get('name', '').strip()

    if name:
        matches = StudentProfile.objects.filter(
            Q(user__first_name__icontains=name) | 
            Q(user__last_name__icontains=name)
        ).select_related('user', 'class_arm')[:10] 
    else:
        matches = []

    return render(request, 'portals/partials/student_list.html', {'matches': matches})


@login_required
@role_required('ADMIN')
def man_teachers(request):
    school = request.user.school
    teachers = TeacherProfile.objects.select_related('user').prefetch_related('subjects', 'class_arms').all()
    if teachers:
        print('ahoy')
        for teacher in teachers:
            print(teacher.user.username)
    return render(request, 'portals/manage_staff.html', {
        'teachers': teachers,
    })


@login_required
@role_required('ADMIN')
def add_teacher(request):
    school = request.user.school

    if request.method == 'POST':
        form = TeacherCreationForm(data=request.POST)
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
@role_required('STUDENT')
def man_subjects(request):
    student = get_object_or_404(StudentProfile.objects.select_related('class_arm'), user=request.user)

    target_categories = _get_student_categories(student)

    if request.method == 'POST':
        form = SubjectEnrollmentForm(request.POST, target_categories=target_categories)

        if form.is_valid():
            selected_subjects = form.cleaned_data['subjects']

            core_subjects = Subject.objects.filter(category__icontains='CORE', id__in=Subject.objects.filter(category__in=target_categories))

            student.subjects.set(selected_subjects | core_subjects)
            messages.success(request, 'Subject Enrollment success!')
            return redirect('portal:show-subjects')
    else:
        form = SubjectEnrollmentForm(student=student, target_categories=target_categories)
    return render(request, 'portals/partials/manage_subjects.html', {'form': form})


@login_required
@role_required('STUDENT')
def show_subjects(request):
    student = get_object_or_404(
        StudentProfile.objects.prefetch_related('subjects'), 
        user=request.user
    )
    subjects = student.subjects.all()

    return render(request, 'portals/partials/subjects_selected.html', {'subjects': subjects})    

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

@login_required
@role_required('ADMIN', 'TEACHER')
def view_student(request, id):
    user = request.user

    student = get_object_or_404(StudentProfile.objects.prefetch_related('user', 'class_arm', 'subjects', 'class_arm__class_level'), id=id)
    if user.role == 'TEACHER':
        if(student.class_arm.class_teacher != request.user):
            raise PermissionDenied('You are not assigned to this students class arm.')
    base_template = None
    if user.role == 'TEACHER':
        base_template = 'portals/teacher_dashboard.html'
    if user.role == 'ADMIN':
        base_template = 'portals/admin_dashboard.html'
    
    context = {
        'student': student,
        'base_template': base_template
    }
    return render(request, 'portals/partials/student_profile.html', context)

@login_required
@role_required('ADMIN')
def view_teacher(request, id):
    user = request.user
    if user.role != 'ADMIN':
        raise PermissionDenied('You are not authorized. you are not the admin dawgg!')
    
    teacher = get_object_or_404(TeacherProfile.objects.prefetch_related( 'class_arms', 'subjects', 'class_arms__class_level'), id=id)

    context = {
        'teacher': teacher
    }

    return render(request, 'portals/partials/teacher_profile.html', context)

def _get_student_categories(student):

    is_junior = 'JSS' in student.class_arm.class_level.name.upper()
    is_senior = 'SSS' in student.class_arm.class_level.name.upper()

    
    arm_name = student.class_arm.name.upper()
    stream = 'ARTS'

    if is_senior:
        if arm_name == 'A':
            stream = 'SCIENCE'
        elif arm_name == 'B':
            stream = 'COMMERCIAL'

    
    category_map = {
        'JUNIOR': ['JNR_CORE', 'JUNIOR'],
        'SCIENCE': ['SNR_CORE', 'SCIENCE', 'VOCATIONAL_TRADE'],
        'COMMERCIAL': ['SNR_CORE', 'COMMERCIAL', 'VOCATIONAL_TRADE'],
        'ARTS': ['SNR_CORE', 'ARTS_HUMANITIES', 'VOCATIONAL_TRADE'],
    }
    
    key= 'JUNIOR'if is_junior else stream

    target_categories = category_map[key]
    
    return target_categories