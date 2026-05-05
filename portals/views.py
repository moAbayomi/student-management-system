from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from django.contrib import messages
from django.db.models import Q
from django.db import transaction   
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .decorators import role_required
import calendar
from datetime import timedelta, date
import plotly.graph_objects as go
import plotly.io as pio
from academics.models import ClassArm, Subject, SubjectAssignment, Result, DailyAttendance
from schools.models import AcademicTerm
from profiles.models import TeacherProfile, StudentProfile
from users.models import User
from .forms import TeacherCreationForm, StudentCreationForm, SubjectEnrollmentForm, ClassArmForm, SubjectAssignmentFormSet, ChangeClassTeacher, UserIdentityForm, TeacherWorkInfoForm, generate_temp_password 


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
    teachers = User.objects.filter(role='TEACHER')
    total_teachers = teachers.count()
    students = User.objects.filter(role='STUDENT')
    total_students = students.count()
    class_arms = ClassArm.objects.all()
    total_class_arms = class_arms.count()
    curr_term = AcademicTerm.objects.get(is_current=True)

    context = {
        'teachers': teachers,
        'total_teachers': total_teachers,
        'students': students,
        'total_students': total_students,
        'class_arms': class_arms,
        'total_class_arms': total_class_arms, 
        'curr_term': curr_term
    }

    return render(request, 'portals/admin_dashboard.html', context)

@login_required
@role_required('TEACHER')
def teacher_dashboard(request):
    teacher = get_object_or_404(TeacherProfile, user=request.user)
    teacher_arm = ClassArm.objects.filter(class_teacher=request.user).first()
    teacher_assignments = SubjectAssignment.objects.filter(teacher=teacher).select_related('subject', 'class_arm', 'session')
    arms = teacher.user.class_teacher_of.all() 
    arm_count = arms.count()
    subject_count = teacher_assignments.count()
    recent_students = StudentProfile.objects.filter(class_arm=teacher_arm).order_by('-id')[:3]

    
    return render(request, 'portals/teacher_dashboard.html', {
        'teacher': teacher,
        'teacher_assignments': teacher_assignments,
        'class_arms': arms,
        'arm_count': arm_count,
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
        'class_arm': class_arm,
        'base_template': 'portals/teacher_dashboard.html'
        })
    elif user.role == 'ADMIN':
        form = ClassArmForm(request.GET)
        students = StudentProfile.objects.select_related('user', 'class_arm', 'class_arm__class_level').all()
        class_arm = None
        if form.is_valid() and form.cleaned_data.get('class_arm'):
            class_arm = form.cleaned_data.get('class_arm')
            students = students.filter(class_arm=class_arm)  

        context = {
            'form': form,
            'students': students,
            'count': students.count(),
            'class_arm': class_arm,
            'base_template': 'portals/admin_dashboard.html'
        }

        return render(request, 'portals/manage_students.html', context)
    

@login_required
@role_required('ADMIN')
def change_classteacher(request, id):
    teacher_profile = get_object_or_404(TeacherProfile, id=id)

    if request.method == 'POST':
        form = ChangeClassTeacher(request.POST, teacher_profile=teacher_profile.user)
        if form.is_valid():
            form.save()
            teacher_user = teacher_profile.user
            teacher_user.refresh_from_db() 
            return redirect('portal:view-teacher', id)
    else:
        form = ChangeClassTeacher(teacher_profile=teacher_profile.user)
    return render(request, 'portals/partials/change_classteacher.html', {'form': form, 'teacher': teacher_profile.user})



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
    teachers = TeacherProfile.objects.select_related('user').prefetch_related('assignments__subject', 'assignments__class_arm').all()
    
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
            profile.user.class_teacher_of.set(form.cleaned_data['class_arms'])

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
    
    teacher = get_object_or_404(TeacherProfile.objects.prefetch_related('assignments__subject', 'assignments__class_arm'), id=id)
    
    context = {
        'teacher': teacher,
    }

    return render(request, 'portals/partials/teacher_profile.html', context)

@login_required
@role_required('ADMIN')
def edit_subjects_taken(request, id):
    teacher_profile = get_object_or_404(TeacherProfile.objects.prefetch_related('assignments__subject', 'assignments__class_arm'), id=id)

    if request.method == 'POST':
        formset = SubjectAssignmentFormSet(request.POST, instance=teacher_profile)

        if formset.is_valid():
            try:
                with transaction.atomic():
                    instances = formset.save(commit=False)
                for obj in formset.deleted_objects:
                    obj.delete()

            # 2. Process each form in the formset
                for form in formset.forms:
                    if not form.cleaned_data or form in formset.deleted_forms:
                        continue

                    assignment = form.save(commit=False)
                    
                    if form.cleaned_data.get('all_arms'):
                        # Get all arms for the level of the selected arm
                        # Example: If SSS1A is selected, find SSS1A, SSS1B, SSS1C
                        level = assignment.class_arm.class_level
                        all_arms = ClassArm.objects.filter(class_level=level)
                        
                        for arm in all_arms:
                            SubjectAssignment.objects.get_or_create(
                                teacher=teacher_profile,
                                subject=assignment.subject,
                                class_arm=arm,
                                session=assignment.session
                            )
                    else:
                        # Save just the single assignment as usual
                        assignment.teacher = teacher_profile
                        assignment.save()
                        
                return redirect('portal:view-teacher', id=teacher_profile.id)
            except Exception as e:
                # Handle unexpected database errors (like unique constraint violations)
                formset.non_form_errors().append(f"Database error: {e}")
    else:
        formset = SubjectAssignmentFormSet(instance=teacher_profile)

    return render(request, 'portals/partials/edit_subjects.html', {
        'formset': formset,
        'teacher': teacher_profile
    })

@login_required
@role_required('ADMIN')
def edit_teacher_details(request, id):
    teacher_profile = get_object_or_404(TeacherProfile, id=id)
    user = teacher_profile.user

    if request.method == 'POST':
        user_form = UserIdentityForm(request.POST, instance=user)
        teacher_pr_form = TeacherWorkInfoForm(request.POST, instance=teacher_profile)

        if user_form.is_valid() and teacher_pr_form.is_valid():
            user_form.save()
            teacher_pr_form.save()
            return redirect('portal:view-teacher', id=id)
    else:
        user_form = UserIdentityForm(instance=user)
        teacher_pr_form = TeacherWorkInfoForm(instance=teacher_profile)

    return render(request, 'portals/partials/edit_teacher.html', {
        'forms': [user_form, teacher_pr_form],
        'teacher': user
    })


@login_required
@role_required('TEACHER')
def bulk_grading_view(request, id):
    assignment = get_object_or_404(SubjectAssignment, id=id)

    term = AcademicTerm.objects.filter(is_current=True).first()

    if not term:
        messages.error(request, "No active academic term found. Please contact Admin.")
        return redirect('some_dashboard_url')
    
    students = StudentProfile.objects.filter(class_arm=assignment.class_arm, subjects=assignment.subject)

    for student in students:
        Result.objects.get_or_create(
            student=student,
            subject_assignment=assignment,
            term=term
        )

    ResultFormSet = modelformset_factory(
        Result,
        fields = ('ca_score', 'exam_score'),
        extra=0
    )

    queryset = Result.objects.filter(subject_assignment=assignment, term=term).select_related('student__user')

    if request.method == 'POST':
        formset = ResultFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, f"Grades for {assignment.subject} updated successfully!")
            return redirect('portal:teacher')
    else:
        formset = ResultFormSet(queryset=queryset)
        
    context = {
        'formset': formset,
        'assignment': assignment,
        'term': term
    }
    return render(request, 'portals/partials/bulk_grading.html', context)

@login_required
@role_required('TEACHER', 'ADMIN')
def class_broadsheet_view(request, id):
    class_arm = get_object_or_404(ClassArm, id=id)
    students = StudentProfile.objects.filter(class_arm=class_arm)
    subjects = SubjectAssignment.objects.filter(class_arm=class_arm)

    matrix = {}
    for student in students:
        matrix[student.id] = {
            'student_name': student.user.get_full_name(),
            'scores': {},
            'average': 0
        }

        results = Result.objects.filter(student=student)
        for r in results:
            matrix[student.id]['scores'][r.subject_assignment.subject.id] = r.total_score
            matrix[student.id]['average'] = sum(matrix[student.id]['scores'].values())/len(matrix[student.id]['scores'].values())

    return render(request, 'portals/partials/broadsheet.html', {
        'matrix': matrix,
        'subjects': subjects,
        'class_arm': class_arm
    })


@login_required
@role_required('TEACHER')
def man_attendance(request, id):

    class_arm = get_object_or_404(ClassArm, id=id)
    monday, week_dates = get_work_week()

    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        term = get_current_term()

        for s_id in student_ids:
            for day in week_dates:
                field_name = f"att_{s_id}_{day.strftime('%Y-%m-%d')}"
                is_present = field_name in request.POST

                DailyAttendance.objects.update_or_create(
                    student=StudentProfile.objects.get(id=s_id),
                    date=day,
                    defaults={
                        'status': 'P' if is_present else 'A',
                        'term': term,
                        'class_arm_id': id
                    }
                )
        return redirect('portal:man-students')
    else:
        students = StudentProfile.objects.filter(class_arm=class_arm)

        for student in students:
            student.present_dates = list(
                student.attendance_records.filter(
                    date__in=week_dates,
                    status='P',
                ).values_list('date', flat=True)
            )

            student.present_dates = [d.strftime('%Y-%m-%d') for d in student.present_dates]


        context = {
            'students': students,
            'class_arm': class_arm,
            'week_dates': week_dates,
            'monday_date': monday
            }
        return render(request, 'portals/partials/attendance.html', context)


@login_required
def view_result(request, id):
    student = get_object_or_404(StudentProfile, id=id)
    results = Result.objects.filter(student=student)

    context = {
        "results": results
    }

    return render(request, 'portals/partials/results.html', context)

def attendance_overview(request, id):
    student = StudentProfile.objects.get(id=id)
    attendance_grid = get_attendance_grid(student)

    x, y, z = format_grid_for_plotly(attendance_grid)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=list(range(len(x))), # Use numbers for spacing
        y=y,
        # Custom Colors: 0 is Red (Absent), 1 is Green (Present)
        colorscale=[[0, '#ef4444'], [1, '#22c55e']], 
        showscale=False,
        xgap=2, ygap=2,
        hoverongaps=False,
    ))

    # Production Styling
    fig.update_layout(
        height=180,
        margin=dict(t=5, b=30, l=5, r=5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickmode='array',
            tickvals=[i for i, label in enumerate(x) if label],
            ticktext=[label for label in x if label],
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(showgrid=False, zeroline=False),
    )

    chart_html = pio.to_html(fig, full_html=False, include_plotlyjs=False, config={'displayModeBar': False})
    
    return render(request, 'portals/partials/attendance_overview.html', {'heatmap': chart_html, 'student': student})


def test_plotly(request):
    fig = go.Figure(data=[go.Bar(x=['A', 'B', 'C'], y=['1', '3', '2'])])

    chart_html = pio.to_html(fig, full_html=False, include_plotlyjs=False)

    return render(request, 'portals/partials/test_chart.html', {'chart_div': chart_html})

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

def get_work_week():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(5)]

    return monday, week_dates


def get_current_term():
    term = AcademicTerm.objects.get(is_current=True)
    return term

def get_attendance_grid(student, year=2026):
    presents = set(student.attendance_records.filter(
        date__year=year,
        status='P'
    ).values_list('date', flat=True))

    grid = {}

    for month in range (1, 13):
        month_name = calendar.month_name[month]
        month_days = calendar.monthcalendar(year, month)

        weeks_in_month = []

        for week in month_days:
            day_data = []
            for i in range(5):
                day_num = week[i]
                if day_num == 0:
                    day_data.append({'status': 'empty'})
                else:
                    d = date(year, month, day_num)
                    status = 'present' if d in presents else 'absent'

                    if d > date.today(): status= 'future'
                    day_data.append({'date': d, 'status': status})
            
            if any(d['status'] != 'empty' for d in day_data):
                weeks_in_month.append(day_data)

        grid[month_name] = weeks_in_month
    return grid

def format_grid_for_plotly(grid_data):
    y_labels = ['Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday']
    z_matrix = [[], [], [], [], []]
    x_labels = []

    for month_name, weeks in grid_data.items():
        for week_idx, week in enumerate(weeks):
            label = month_name if week_idx == 0 else ''
            x_labels.append(label)

            for i in range(5):
                day = week[i]

                if day['status'] == 'present':
                    val = 1
                elif day['status'] == 'absent':
                    val = 0
                else:
                    val = None
                
                z_matrix[4 - i].append(val)
    
    return x_labels, y_labels, z_matrix
