from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
import uuid
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.forms import modelformset_factory
from django.contrib import messages
from django.db.models import Q
from django.db import transaction   
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
import calendar
from datetime import timedelta, date as python_date, datetime
from .services import AdminOverviewAggregator, AdminStudentOverviewAggregator, AdminTeacherOverviewAggregator, AdminClassConsoleOverviewAggregator, TeacherOverviewAggregator, TeacherAttendanceOverviewAggregator, TeacherSubjectAssignmentOverViewAggregator
from profiles.services import StudentProfileService, TeacherProfileService, StudentRegistrationService, TeacherRegistrationService, TeacherOnboardingService, StudentOnboardingService
from academics.services import AcademicsManagementService
import plotly.graph_objects as go
import plotly.io as pio
from academics.models import ClassArm, Subject, SubjectAssignment, Class, DailyAttendance
from schools.models import AcademicSession, AcademicTerm, get_school
from schools.forms import AcademicSessionForm
from profiles.models import TeacherProfile, StudentProfile
from users.models import User
from .forms import TeacherCreationForm, StudentCreationForm, NewArm, AssignClassTeacher, CoreSubjects, SchoolSettingsForm
import json



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
    context = AdminOverviewAggregator.get_complete_overview()
    return render(request, 'portals/admin/admin.html', context)

@login_required
@role_required('TEACHER')
def teacher_dashboard(request):
    context = TeacherOverviewAggregator.get_complete_overview(request.user)
    return render(request, 'portals/teacher/teacher.html', context)

@login_required
@role_required('TEACHER')
def teachers_view_students(request):
    if request.headers.get('HX-Request'):
        search = request.GET.get('q')
        page_no= request.GET.get('page', 1)

        print(search)
        context = TeacherOverviewAggregator.get_paginated_students(request.user, page_no=page_no, search_query=search)
        html = render_to_string('portals/teacher/my_students/partials/_student_table.html', context, request=request)
        return HttpResponse(html)
    context = TeacherOverviewAggregator.get_paginated_students(request.user)
    return render(request, 'portals/teacher/my_students/my_students.html', context)

@login_required
@role_required('TEACHER')
def attendance_teacher(request):
    context = TeacherAttendanceOverviewAggregator.get_attendance_overview(request.user)
    return render(request, 'portals/teacher/attendance/attendance.html', context)

@login_required
@role_required('TEACHER')
def arm_attendance_data(request, arm_id):
    class_arm = get_object_or_404(ClassArm, id=arm_id)
    today = python_date.today()
    date = request.GET.get('curr-date', str(today))
    print(date)
    try:
        date = python_date.fromisoformat(date)
    except ValueError:
        return JsonResponse({'error': 'invalid response'}, status=400)
    
    students_qs = class_arm.students.select_related('user').all()

    attendance_records = DailyAttendance.objects.filter(
        class_arm=class_arm, date=date
    ).values('student_id', 'status', 'remarks', 'date')

    record_map = {rec['student_id']: (rec['status'], rec['remarks'], rec['date']) for rec in attendance_records}
    
    
    # Build the response list
    students_list = []
    for student in students_qs:
        status, remarks, date = record_map.get(student.id, ('P', ''))  # default to Present if no record
        students_list.append({
            'id': student.id,
            'name': student.user.get_full_name(),
            'admission_number': student.admission_number or '',
            'initials': student.user.get_full_name()[:2].upper(),  # first two letters, adjust if needed
            'status': status,
            'remarks': remarks,
        })
    
    return JsonResponse(students_list, safe=False)

@login_required
@role_required('TEACHER')
def save_attendance(request, arm_id):
    arm = get_object_or_404(ClassArm, pk=arm_id)
    term = get_object_or_404(AcademicTerm, is_current=True)
    try:
        data = json.loads(request.body)
        target_date = python_date.fromisoformat(data['date'])
        records = data.get('records', [])
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    # Optional: verify that the arm belongs to the logged‑in user's school
    # if arm.class_level.school != request.user.school: ...

    for rec in records:
        DailyAttendance.objects.update_or_create(
            student_id=rec['student_id'],
            class_arm=arm,
            date=target_date,
            term=term,
            defaults={
                'status': rec['status'],
                'remarks': rec.get('remarks', ''),
                'updated_by': request.user
            }
        )

    return JsonResponse({'success': True})


@login_required
@role_required('STUDENT')
def student_dashboard(request):
    from profiles.models import StudentProfile
    profile = StudentProfile.objects.select_related(
        'class_arm', 'class_arm__class_level', 'class_arm__class_teacher'
    ).get(user=request.user)

    return render(request, 'portals/student/student_dashboard.html', {
        'profile': profile,
    })

@login_required
@role_required('ADMIN')
def students_directory(request):
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('search')
    class_filter = request.GET.get('class_level', 'All Classes')

    if request.headers.get('HX-Request'):
        context = StudentProfileService.get_paginated_students(page_no=page_number, search_query=search_query, class_filter=class_filter)
        table_html = render_to_string('portals/admin/students/partials/students_table.html', context, request=request)

        return HttpResponse(table_html)
    context = AdminStudentOverviewAggregator.get_student_overview(page_number)
    return render(request, 'portals/admin/students/students_directory.html', context)


@login_required
@role_required('ADMIN', 'TEACHER')
def student_detail(request, id):
    context = StudentProfileService.get_student(id)
    if request.headers.get('Trigger-Source') == 'sidebar-update':
        return render(request, 'portals/partials/shared/student_card_right_sidebar.html', context)
    
    return render(request, 'portals/admin/students/student_profile.html', context)

@login_required
@role_required('ADMIN')
def create_student(request):
    if request.method == 'POST':
        save_mode = request.POST.get('save_mode', 'complete')
        form = StudentCreationForm(request.POST)

        if save_mode == 'draft':
            required_fields = ['first_name', 'last_name', 'dob', 'gender']

            if all(request.POST.get(fields) for fields in required_fields):
                std = StudentRegistrationService.create_draft_student(request.POST)
                row_html = render_to_string('portals/admin/students/partials/student-table-row.html', {'std': std}, request=request)
                
                response_payload = (
                    f'<tbody id="student-table-body" class="divide-y divide-[var(--color-border-light)]/50" hx-swap-oob="afterbegin">{row_html}</tbody>'
                    f'<div id="modal-container" hx-swap-oob="innerHTML"></div>'
                )

                print('student created', std.user.first_name)
                return HttpResponse(response_payload)
            else:
                return HttpResponse('missing required params to complete draft reg')

        if form.is_valid():
            std_profile = StudentRegistrationService.create_complete_student(form)
            row_html = render_to_string('portals/admin/students/partials/student-table-row.html', {'std': std_profile}, request=request)
                
            response_payload = (
                    f'<tbody id="student-table-body" class="divide-y divide-[var(--color-border-light)]/50" hx-swap-oob="afterbegin">{row_html}</tbody>'
                    f'<div id="modal-container" hx-swap-oob="innerHTML"></div>'
                )

            print('student created', std_profile)
            return HttpResponse(response_payload)
        else:
            return HttpResponse('missing required params to complete draft reg')

    else:
        form = StudentCreationForm()

    return render(request, 'portals/admin/students/partials/create_student_modal.html', {'form': form})

@transaction.atomic
def onboard_student(request, token):
    student, status = StudentOnboardingService.get_valid_student_and_status(token)
    print(student, status)

    if status == 'already_active':
        return redirect('users:login')
    if status == 'expired':
        return render(request, 'portals/admin/students/partials/token_expired.html', {'message': 'this is expired. you can regenerate another one. okay', 'student': student})
    if status == 'invalid':
        return render(request, 'portals/admin/students/partials/link_invalid.html'), {'message': 'what can i say? nothing for you dawg'}

    if request.method == 'POST':
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm or not password or not password_confirm:
            print('hell foking no')
            return render(request, 'portals/admin/students/partials/onboarding_set_password.html', {'token': token})
        StudentOnboardingService.set_student_password(student, password)
        login_url = reverse('users:login')

        return HttpResponse(f"Password set successfully. You can now <a href='{login_url}'>log in</a>.")


    
    return render(request, 'portals/admin/students/partials/onboarding_set_password.html', {'token': token})

@transaction.atomic
def resend_student_token(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id, status='PENDING_REVIEW')
    StudentOnboardingService.renegerate_onboarding_token(student)
    StudentRegistrationService.send_student_onboarding_email(student)

    return render(request, 'portals/admin/students/partials/link_sent.html')


@login_required
@role_required('ADMIN')
def edit_student(request, id):
    student = StudentProfile.objects.get(id=id)
    if request.method == 'POST':
        save_mode = request.POST.get('save_mode', 'complete')
        form = StudentCreationForm(request.POST)
        print('okay, wagwan')
        if save_mode == 'draft':
            required_fields = ['first_name', 'last_name', 'dob', 'gender']

            if all(request.POST.get(fields) for fields in required_fields):
                std = StudentRegistrationService.edit_draft_student(id, request.POST)
                row_html = render_to_string('portals/admin/students/partials/student-table-row.html', {'std': std, 'oob': True}, request=request)
                print(std)
                response_payload = (
                    f'{row_html}<div id="modal-container" hx-swap-oob="innerHTML"></div>'
                )

                print('student edited', std.user.first_name)
                return HttpResponse(response_payload)
            else:
                return HttpResponse('missing required params to complete draft reg')
        if form.is_valid():
            std_profile = StudentRegistrationService.edit_complete_student(id, form)
            row_html = render_to_string('portals/admin/students/partials/student-table-row.html', {'std': std_profile, 'oob': True}, request=request)
                
            response_payload = (
                    f'<tbody id="student-table-body" class="divide-y divide-[var(--color-border-light)]/50" hx-swap-oob="afterbegin">{row_html}</tbody>'
                    f'<div id="modal-container" hx-swap-oob="innerHTML"></div>'
                )

            return HttpResponse(response_payload)
        else:
        
            return HttpResponse(
                    status=204, 
                    headers={'HX-Trigger': 'refreshStudentTable'}
                )
            
    else:
        initial = StudentRegistrationService.get_initial_data(id)
        form = StudentCreationForm(initial=initial)
    return render(request, 'portals/admin/students/partials/create_student_modal.html', {'form': form, 'student': student, 'edit': True})



@login_required
@role_required('ADMIN')
def teachers_directory(request):
    page_no = request.GET.get('page', 1)
    search = request.GET.get('search')

    if request.headers.get('HX-Request'):
        context = TeacherProfileService.get_paginated_teachers(page_no=page_no, search_query=search)
        return render(request, 'portals/admin/teachers/partials/teachers_table.html', context)
    
    context = AdminTeacherOverviewAggregator.get_teachers_overview(page_no)
    
    return render(request, 'portals/admin/teachers/teachers_directory.html', context)


@login_required
@role_required('ADMIN')
def teacher_detail(request, id):
    context = {**TeacherProfileService.get_details(id), **AcademicsManagementService.get_stats()}
    if request.headers.get('Trigger-Source') == 'sidebar-update':
        return render(request, 'portals/admin/teachers/partials/teacher_card_right_sidebar.html', context)
    
    return render(request, 'portals/admin/teachers/teacher_profile.html', context)


@login_required
@role_required('ADMIN')
def create_teacher(request):
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)

        if form.is_valid():
            teacher_profile = TeacherRegistrationService.create_full_teacher(form)
            row_html = render_to_string('portals/admin/teachers/partials/teacher_table_row.html', {'teacher': teacher_profile}, request=request)
            response_payload = (
                f'<tbody id="teachers-table-body" hx-swap-oob="afterbegin" class="divide-y divide-[var(--color-border-light)]/50">{row_html}</tbody>'
                f'<div id="modal-container" hx-swap-oob="innerHTML"></div>'
            )

            return HttpResponse(response_payload)
        else:
            return HttpResponse('omo something don sup for inside your form or somewhere sha. your from no dey valid. fix up!!')


    else:
        form = TeacherCreationForm()
        departments = form.fields['department'].choices
        subjects = form.fields['subjects'].queryset
    return render(request, 'portals/admin/teachers/partials/create_teacher_modal.html', {'form': form, 'subjects': subjects, 'departments': departments})

@transaction.atomic
def teacher_onboard(request, token):
    teacher, status = TeacherOnboardingService.get_valid_teacher_and_status(token)

    if status == 'invalid':
        return render(request, 'portals/admin/teachers/partials/link_invalid.html', {'message': 'alright what is this? is this whole thing a joke to you? what are you even trying to do?'})

    if status == 'already-active':
        return redirect('users:login')
    
    if status == 'expired':
        return render(request, 'portals/admin/teachers/partials/token_expired.html', {'message': 'this token is expired baby, do something', 'teacher': teacher})
    
    if request.method == 'POST':
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            return render(request, 'public/set_password.html', {'error': 'Passwords do not match.', 'token': token})
        TeacherOnboardingService.set_teacher_password(teacher, password)
        login_url = reverse('users:login')

        return HttpResponse(f"Password set successfully. You can now <a href='{login_url}'>log in</a>.")
    
    return render(request, 'portals/admin/teachers/partials/onboarding_set_password.html', {'token': token})



@transaction.atomic
def resend_teacher_token(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id, status='PENDING_REVIEW')

    TeacherOnboardingService.regenerate_onboarding_token(teacher)
    TeacherRegistrationService.send_onboarding_email(teacher)

    return render(request, 'portals/admin/teachers/partials/link_sent.html')



@login_required
@role_required('ADMIN')
def edit_teacher(request, id):
    teacher_profile = TeacherProfile.objects.get(id=id)
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            teacher_profile = TeacherRegistrationService.edit_complete_student(id, form)

            row_html = render_to_string('portals/admin/teachers/partials/teacher_table_row.html', {'teacher': teacher_profile, 'oob':True}, request=request)

            response_payload = (
                    f'<tbody id="teachers-table-body" hx-swap-oob="afterbegin" class="divide-y divide-[var(--color-border-light)]/50">{row_html}</tbody>'
                    f'<div id="modal-container" hx-swap-oob="innerHTML"></div>'
                )

            return HttpResponse(response_payload)
        else:
            return HttpResponse('omo something don sup for inside your form or somewhere sha. your from no dey valid. fix up!!')

    else:
        initial = TeacherRegistrationService.get_initial_data(id)
        form = TeacherCreationForm(initial=initial)
    return render(request, 'portals/admin/teachers/partials/create_teacher_modal.html', {'form': form, 'teacher': teacher_profile, 'edit': True, **initial})

@login_required
@role_required('ADMIN')
def assign_teacher_subject(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        subject_id = request.POST.get('subject_id')
        class_arms = request.POST.getlist('arms')
        session = AcademicSession.objects.get(is_current=True)

        if not all(['teacher_id', 'subject_id', 'class_arms']):
            return HttpResponse('what is wrong with you bro??', status=400)
        
        teacher = get_object_or_404(TeacherProfile, id=teacher_id)
        subject = get_object_or_404(Subject, id=subject_id)

        for arm_id in class_arms:
            class_arm = get_object_or_404(ClassArm, id=arm_id)
            assignment, created = SubjectAssignment.objects.update_or_create(
             subject=subject,
             class_arm=class_arm,
             session=session,
             defaults={'teacher': teacher}   
            )
        
        return HttpResponse("<p class='text-xs text-green-600 font-bold'>Teacher assigned successfully.</p>")


@login_required
@role_required('ADMIN')
def load_subjects(request):
    dept = request.GET.get('department')
    dept_query = {
        'JUNIOR': ['JNR_CORE', 'JUNIOR'],
        'SCIENCE': ['SNR_CORE', 'SCIENCE', 'VOCATIONAL_TRADE'],
        'ARTS_HUMANITIES': ['SNR_CORE', 'ARTS', 'VOCATIONAL_TRADE'],
        'COMMERCIAL': ['SNR_CORE', 'COMMERCIAL', 'VOCATIONAL_TRADE'],
        'VOCATIONAL_TRADE': ['SNR_CORE', 'VOCATIONAL_TRADE']
    }

    if dept:
        subjects = Subject.objects.filter(category__in=dept_query[dept])    

    return render(request, 'portals/admin/teachers/partials/subject_checkboxes.html', {'subjects': subjects, 'selected_subject_ids': request.GET.getlist('selected')})


@login_required
@role_required('ADMIN')
def load_arms(request):
    class_level_id = request.GET.get('class_level_id')
    if not class_level_id:
        return HttpResponse('<option value="">-- Select class level first --</option>')
    
    try:
        class_obj = Class.objects.get(id=class_level_id)
    except Class.DoesNotExist:
        HttpResponse("<option value=''>invalid class level</option>")

    class_arm = ClassArm.objects.filter(class_level=class_obj)
    html = ''
    for arm in class_arm:
        html += f'<label class="flex items-center gap-1.5 text-[11.5px] text-main cursor-pointer"> <input type="checkbox" name="arms" value="{arm.id}" class="accent-main" /> {arm.name} </label>'
    return HttpResponse(html)



@login_required
@role_required('ADMIN')
def class_console(request):
    context = AdminClassConsoleOverviewAggregator.get_class_console_overview()   
    return render(request, 'portals/admin/class_console/class_console.html', context)

@login_required
@role_required('ADMIN')
def class_details(request, class_id):
    curr_class = get_object_or_404(Class, id=class_id)
    html = render_to_string('portals/admin/class_console/partials/class_details.html', {'class': curr_class}, request=request)
    return HttpResponse(html)

@login_required
@role_required('ADMIN')
def arm_details(request, arm_id):
    arm = get_object_or_404(ClassArm, id=arm_id)
    subject_assignments = SubjectAssignment.objects.filter(class_arm=arm)
    return render(request, 'portals/admin/class_console/partials/arm_details_panel.html', {'arm': arm, 'subject_assignments': subject_assignments})

@login_required
@role_required('ADMIN')
def load_core_subjects(request, arm_id):
    arm = get_object_or_404(ClassArm, id=arm_id)
    curr_session = AcademicSession.objects.get(is_current=True)
    class_level = arm.class_level

    for subject in class_level.core_subjects.all():
        SubjectAssignment.objects.get_or_create(
            class_arm=arm,
            subject=subject,
            session=curr_session,
            defaults={'teacher': None}
        )

    subject_assignments = arm.subject_assignments.filter(session=curr_session).select_related('subject', 'teacher')
    return render(request, 'portals/admin/class_console/partials/_subject_assignments_list.html', {'subject_assignments': subject_assignments})

@login_required
@role_required('ADMIN')
def manage_arm_core_subjects(request, class_id):
    curr_class = get_object_or_404(Class, id=class_id)

    if request.method == 'POST':
        form = CoreSubjects(request.POST)
        if form.is_valid():
            curr_class.core_subjects.set(form.cleaned_data['core_subjects'])
            html = render_to_string('portals/admin/class_console/partials/class_details.html', {'class': curr_class,}, request=request)
            return HttpResponse(html)
    else:
        initial_subjects = curr_class.core_subjects.all()
        form = CoreSubjects(initial={'core_subjects':initial_subjects})
        subjects = Subject.objects.all()
        html = render_to_string('portals/admin/class_console/partials/manage_arm_core_subjects.html', {'class': curr_class, 'subjects': subjects, 'form': form}, request=request)
    return HttpResponse(html)

@login_required
@role_required('ADMIN')
def add_arm(request, level_id):
    level = get_object_or_404(Class, id=level_id)

    if request.method == 'POST':
        form = NewArm(request.POST)
        if form.is_valid():
            arm_name = form.cleaned_data['name']
            ClassArm.objects.create(
                class_level=level,
                name=arm_name,
            )
            return render(request, 'portals/admin/class_console/partials/arm_grid.html', {'arm': ClassArm.objects.get(class_level=level, name=arm_name)})
        else:
            return render(request, 'portals/admin/class_console/partials/add_arm.html', {'form': form, 'level': level})
    else:
        form = NewArm()
    return render(request, 'portals/admin/class_console/partials/add_arm.html', {'form': form, 'level': level})

@login_required
@role_required('ADMIN')
def delete_arm(request, arm_id):
    arm = get_object_or_404(ClassArm, id=arm_id)
    arm.delete()
    return HttpResponse(status=200)

@login_required
@role_required('ADMIN')
def assign_arm_class_teacher(request, arm_id):
    arm = get_object_or_404(ClassArm, id=arm_id)
    if request.method == 'POST':
        form = AssignClassTeacher(request.POST)
        if form.is_valid():
            teacher = form.cleaned_data['teacher']
            arm.class_teacher = teacher
            arm.save()
            html = render_to_string('portals/admin/class_console/partials/arm_teacher_card.html', {'arm': arm}, request=request)
            return HttpResponse(html)
    else:
        form = AssignClassTeacher()
    return render(request, 'portals/admin/class_console/partials/assign_teacher_form.html', {'form': form, 'arm': arm})

@login_required
@role_required('ADMIN')
def remove_arm_class_teacher(request, arm_id):
    arm = get_object_or_404(ClassArm, id=arm_id)
    arm.class_teacher = None
    arm.save()
    return render(request, 'portals/admin/class_console/partials/arm_teacher_card.html', {'arm': arm})


@login_required
@role_required('ADMIN')
def admin_attendance(request):
    return render(request, 'portals/admin/attendance/attendance.html')

@login_required
@role_required('ADMIN')
def admin_result_view(request):
    return render(request, 'portals/admin/results/results.html')

@login_required
@role_required('ADMIN')
def admin_annoucements_view(request):
    return render(request, 'portals/admin/announcements/announcements.html')

@login_required
@role_required('ADMIN')
def fees_view(request):
    return render(request, 'portals/admin/fees/fees.html')


@login_required
@role_required('ADMIN')
def admin_settings_view(request):
    return render(request, 'portals/admin/settings/settings.html')



def subject_assignments_view(request):
    context = TeacherSubjectAssignmentOverViewAggregator.get_subject_assignments_overview(user=request.user)
    print(context)
    return render(request, 'portals/teacher/subject_assignments/subject_assignments.html', context)

def results_view(request):
    return render(request, 'portals/teacher/results/results.html')


@login_required
@role_required('ADMIN')
def school_settings(request):
    school = get_school()

    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, 'School settings updated.')
            return redirect('portal:school-settings')
    else:
        form = SchoolSettingsForm(instance=school)

    return render(request, 'portals/admin/settings/school.html', {
        'form': form,
        'school': school,
    })

    
@login_required
@role_required('ADMIN')
def session_list(request):
    sessions = AcademicSession.objects.prefetch_related('terms').all()
    return render(request, 'portals/admin/settings/sessions.html', {
        'sessions': sessions,
        'form': AcademicSessionForm(),
        # 'school': get_school(),
    })


@login_required
@role_required('ADMIN')
def session_create(request):
    if request.method != 'POST':
        return redirect('portal:session-list')

    form = AcademicSessionForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            session = form.save(commit=False)
            session.status = AcademicSession.SessionStatus.PLANNING
            session.is_current = False
            session.save()
            session.create_default_terms()
        messages.success(request, f"Session {session.name} created with 3 terms.")
    else:
        messages.error(request, "Could not create session. Please check the form.")
    return redirect('portal:session-list')


@login_required
@role_required('ADMIN')
@require_POST
def session_set_current(request, session_id):
    session = get_object_or_404(AcademicSession, pk=session_id)
    session.make_current()
    messages.success(request, f"{session.name} is now the current session.")
    return redirect('portal:session-list')