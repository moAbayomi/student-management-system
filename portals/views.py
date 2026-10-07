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
from django.db.models import ProtectedError
from django.utils.html import format_html_join
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
import calendar
from datetime import timedelta, date as python_date, datetime
from .services import AdminOverviewAggregator, AdminStudentOverviewAggregator, AdminTeacherOverviewAggregator, AdminClassConsoleOverviewAggregator, TeacherOverviewAggregator, TeacherAttendanceOverviewAggregator, TeacherSubjectAssignmentOverViewAggregator
from profiles.services import StudentProfileService, TeacherProfileService, StudentRegistrationService, TeacherRegistrationService
from academics.services import AcademicsManagementService
import plotly.graph_objects as go
import plotly.io as pio
from academics.models import ClassArm, Subject, SubjectAssignment, Class, DailyAttendance
from schools.models import AcademicSession, AcademicTerm
from schools.services import get_school, get_current_session, get_current_term
from schools.forms import AcademicSessionForm
from profiles.models import TeacherProfile, StudentProfile
from users.models import User
from .forms import TeacherCreationForm, StudentCreationForm, NewArm, AssignClassTeacher, CoreSubjects, SchoolSettingsForm
import json


def _teacher_profile(user):
    return get_object_or_404(TeacherProfile, user=user)


def _get_form_teacher_arm(request, arm_id):
    """The arm, but only if the logged-in teacher is its form (class) teacher."""
    arm = get_object_or_404(ClassArm, id=arm_id)
    if arm.class_teacher_id != _teacher_profile(request.user).id:
        raise PermissionDenied
    return arm


def _teacher_can_view_student(user, student):
    """A teacher may see students in an arm they form-teach or teach a subject in."""
    teacher = _teacher_profile(user)
    if student.class_arm_id is None:
        return False
    return (
        student.class_arm.class_teacher_id == teacher.id
        or SubjectAssignment.objects.filter(teacher=teacher, class_arm_id=student.class_arm_id).exists()
    )


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
    class_arm = _get_form_teacher_arm(request, arm_id)
    today = python_date.today()
    date = request.GET.get('curr-date', str(today))
    try:
        date = python_date.fromisoformat(date)
    except ValueError:
        return JsonResponse({'error': 'invalid date'}, status=400)
    
    students_qs = class_arm.students.select_related('user').all()

    attendance_records = DailyAttendance.objects.filter(
        class_arm=class_arm, date=date
    ).values('student_id', 'status', 'remarks', 'date')

    record_map = {rec['student_id']: (rec['status'], rec['remarks']) for rec in attendance_records}

    # Build the response list
    students_list = []
    for student in students_qs:
        status, remarks = record_map.get(student.id, ('P', ''))  # default to Present if no record
        students_list.append({
            'id': student.id,
            'name': student.user.get_full_name(),
            'admission_number': student.admission_number or '',
            'initials': student.user.get_full_name()[:2].upper(),  # first two letters, adjust if needed
            'status': status,
            'remarks': remarks or '',
        })
    
    return JsonResponse(students_list, safe=False)

@login_required
@role_required('TEACHER')
@require_POST
def save_attendance(request, arm_id):
    arm = _get_form_teacher_arm(request, arm_id)
    term = get_current_term()
    if term is None:
        return JsonResponse({'error': 'No current term is set. Ask the admin to set one.'}, status=400)

    try:
        data = json.loads(request.body)
        target_date = python_date.fromisoformat(data['date'])
        records = data.get('records', [])
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    if target_date > python_date.today():
        return JsonResponse({'error': "You can't mark attendance for a future date."}, status=400)

    valid_statuses = {code for code, _ in DailyAttendance.STATUS_CHOICES}
    arm_student_ids = set(arm.students.values_list('id', flat=True))
    for rec in records:
        if rec.get('student_id') not in arm_student_ids or rec.get('status') not in valid_statuses:
            return JsonResponse({'error': 'Invalid student or status in records'}, status=400)

    with transaction.atomic():
        for rec in records:
            # (student, date) is unique, so look up by exactly that
            DailyAttendance.objects.update_or_create(
                student_id=rec['student_id'],
                date=target_date,
                defaults={
                    'class_arm': arm,
                    'term': term,
                    'status': rec['status'],
                    'remarks': rec.get('remarks', ''),
                    'updated_by': request.user,
                }
            )

    return JsonResponse({'success': True})


@login_required
@role_required('STUDENT')
def student_dashboard(request):
    profile = get_object_or_404(
        StudentProfile.objects.select_related('class_arm', 'class_arm__class_level', 'class_arm__class_teacher'),
        user=request.user,
    )

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
    student = get_object_or_404(StudentProfile, id=id)
    if request.user.role == 'TEACHER' and not _teacher_can_view_student(request.user, student):
        raise PermissionDenied
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

            return HttpResponse(response_payload)
        else:
            return HttpResponse('missing required params to complete draft reg')

    else:
        form = StudentCreationForm()

    return render(request, 'portals/admin/students/partials/create_student_modal.html', {'form': form})

@login_required
@role_required('ADMIN')
def edit_student(request, id):
    student = get_object_or_404(StudentProfile, id=id)
    if request.method == 'POST':
        save_mode = request.POST.get('save_mode', 'complete')
        form = StudentCreationForm(request.POST)
        if save_mode == 'draft':
            required_fields = ['first_name', 'last_name', 'dob', 'gender']

            if all(request.POST.get(fields) for fields in required_fields):
                std = StudentRegistrationService.edit_draft_student(id, request.POST)
                row_html = render_to_string('portals/admin/students/partials/student-table-row.html', {'std': std, 'oob': True}, request=request)
                response_payload = (
                    f'{row_html}<div id="modal-container" hx-swap-oob="innerHTML"></div>'
                )

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
            return HttpResponse('Some fields are missing or invalid. Please check the form.', status=400)


    else:
        form = TeacherCreationForm()
        departments = form.fields['department'].choices
        subjects = form.fields['subjects'].queryset
    return render(request, 'portals/admin/teachers/partials/create_teacher_modal.html', {'form': form, 'subjects': subjects, 'departments': departments})

@login_required
@role_required('ADMIN')
def edit_teacher(request, id):
    teacher_profile = get_object_or_404(TeacherProfile, id=id)
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            teacher_profile = TeacherRegistrationService.edit_complete_teacher(id, form)

            row_html = render_to_string('portals/admin/teachers/partials/teacher_table_row.html', {'teacher': teacher_profile, 'oob':True}, request=request)

            response_payload = (
                    f'<tbody id="teachers-table-body" hx-swap-oob="afterbegin" class="divide-y divide-[var(--color-border-light)]/50">{row_html}</tbody>'
                    f'<div id="modal-container" hx-swap-oob="innerHTML"></div>'
                )

            return HttpResponse(response_payload)
        else:
            return HttpResponse('Some fields are missing or invalid. Please check the form.', status=400)

    else:
        initial = TeacherRegistrationService.get_initial_data(id)
        form = TeacherCreationForm(initial=initial)
    return render(request, 'portals/admin/teachers/partials/create_teacher_modal.html', {'form': form, 'teacher': teacher_profile, 'edit': True, **initial})

@login_required
@role_required('ADMIN')
@require_POST
def assign_teacher_subject(request):
    teacher_id = request.POST.get('teacher_id')
    subject_id = request.POST.get('subject_id')
    class_arm_ids = request.POST.getlist('arms')

    # Check the actual values (not the strings 'teacher_id', etc., which are always truthy)
    if not (teacher_id and subject_id and class_arm_ids):
        return HttpResponse("<p class='text-xs text-red-600 font-bold'>Pick a subject and at least one arm.</p>", status=400)

    session = get_current_session()
    if session is None:
        return HttpResponse("<p class='text-xs text-red-600 font-bold'>Set a current session in Settings first.</p>", status=400)

    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    subject = get_object_or_404(Subject, id=subject_id)
    class_arms = ClassArm.objects.filter(id__in=class_arm_ids)

    with transaction.atomic():
        for class_arm in class_arms:
            SubjectAssignment.objects.update_or_create(
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

    subjects = Subject.objects.filter(category__in=dept_query.get(dept, [])) if dept else Subject.objects.none()

    return render(request, 'portals/admin/teachers/partials/subject_checkboxes.html', {'subjects': subjects, 'selected_subject_ids': request.GET.getlist('selected')})


@login_required
@role_required('ADMIN')
def load_arms(request):
    class_level_id = request.GET.get('class_level_id')
    if not class_level_id:
        return HttpResponse('<option value="">-- Select class level first --</option>')
    
    class_arms = ClassArm.objects.filter(class_level_id=class_level_id)
    # format_html_join escapes arm.name, so a name like "<script>" can't inject HTML
    html = format_html_join(
        '',
        '<label class="flex items-center gap-1.5 text-[11.5px] text-main cursor-pointer"> <input type="checkbox" name="arms" value="{}" class="accent-main" /> {} </label>',
        ((arm.id, arm.name) for arm in class_arms),
    )
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
    curr_session = get_current_session()
    if curr_session is None:
        return HttpResponse("<p class='text-xs text-red-600 font-bold'>Set a current session in Settings first.</p>")
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
            arm_name = form.cleaned_data['name'].strip().upper()
            if ClassArm.objects.filter(class_level=level, name__iexact=arm_name).exists():
                form.add_error('name', f'{level.name}{arm_name} already exists.')
                return render(request, 'portals/admin/class_console/partials/add_arm.html', {'form': form, 'level': level})
            arm = ClassArm.objects.create(class_level=level, name=arm_name)
            return render(request, 'portals/admin/class_console/partials/arm_grid.html', {'arm': arm})
        else:
            return render(request, 'portals/admin/class_console/partials/add_arm.html', {'form': form, 'level': level})
    else:
        form = NewArm()
    return render(request, 'portals/admin/class_console/partials/add_arm.html', {'form': form, 'level': level})

@login_required
@role_required('ADMIN')
@require_http_methods(['DELETE', 'POST'])
def delete_arm(request, arm_id):
    arm = get_object_or_404(ClassArm, id=arm_id)
    try:
        arm.delete()
    except ProtectedError:
        # StudentProfile.class_arm uses on_delete=PROTECT
        return HttpResponse(f'{arm} still has students. Move them to another arm first.', status=400)
    return HttpResponse(status=200)

@login_required
@role_required('ADMIN')
def assign_arm_class_teacher(request, arm_id):
    arm = get_object_or_404(ClassArm, id=arm_id)
    if request.method == 'POST':
        form = AssignClassTeacher(request.POST)
        if form.is_valid():
            teacher = form.cleaned_data['teacher']
            if teacher.class_teacher_of.exclude(id=arm.id).exists():
                form.add_error('teacher', f'{teacher} is already form teacher of {teacher.class_teacher_of.first()}.')
                return render(request, 'portals/admin/class_console/partials/assign_teacher_form.html', {'form': form, 'arm': arm})
            arm.class_teacher = teacher
            arm.save()
            html = render_to_string('portals/admin/class_console/partials/arm_teacher_card.html', {'arm': arm}, request=request)
            return HttpResponse(html)
    else:
        form = AssignClassTeacher()
    return render(request, 'portals/admin/class_console/partials/assign_teacher_form.html', {'form': form, 'arm': arm})

@login_required
@role_required('ADMIN')
@require_POST
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



@login_required
@role_required('TEACHER')
def subject_assignments_view(request):
    context = TeacherSubjectAssignmentOverViewAggregator.get_subject_assignments_overview(user=request.user)
    return render(request, 'portals/teacher/subject_assignments/subject_assignments.html', context)

@login_required
@role_required('TEACHER')
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