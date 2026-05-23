from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.forms import modelformset_factory
from django.contrib import messages
from django.db.models import Q
from django.db import transaction   
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.template.loader import render_to_string
import calendar
from datetime import timedelta, date, datetime
from .services import AdminOverviewAggregator, AdminStudentOverviewAggregator, AdminTeacherOverviewAggregator
from profiles.services import StudentProfileService, TeacherProfileService, StudentRegistrationService, TeacherRegistrationService
import plotly.graph_objects as go
import plotly.io as pio
from academics.models import ClassArm, Subject, SubjectAssignment, Result, DailyAttendance
from schools.models import AcademicTerm
from profiles.models import TeacherProfile, StudentProfile
from users.models import User
from .forms import TeacherCreationForm, StudentCreationForm
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
    teacher = get_object_or_404(TeacherProfile, user=request.user)
    teacher_arm = ClassArm.objects.filter(class_teacher=request.user).first()
    teacher_assignments = SubjectAssignment.objects.filter(teacher=teacher).select_related('subject', 'class_arm', 'session')
    arms = teacher.user.class_teacher_of.all() 
    arm_count = arms.count()
    subject_count = teacher_assignments.count()
    recent_students = StudentProfile.objects.filter(class_arm=teacher_arm).order_by('-id')[:3]
    my_date = datetime.now().date().strftime("%A, %-d, %B %Y").lower()

    
    return render(request, 'portals/teacher/teacher_dashboard.html', {
        'teacher': teacher,
        'teacher_assignments': teacher_assignments,
        'class_arms': arms,
        'arm_count': arm_count,
        'subject_count': subject_count,
        'recent_students': recent_students,
        "my_date": my_date
        })

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
        print(f"HTMX Filter Triggered. Payload: {context}")
        table_html = render_to_string('portals/admin/students/partials/students_table.html', context, request=request)

        return HttpResponse(table_html)
    context = AdminStudentOverviewAggregator.get_student_overview(page_number)
    return render(request, 'portals/admin/students/students_directory.html', context)


@login_required
@role_required('ADMIN')
def student_detail(request, id):
    context = StudentProfileService.get_student(id)
    if request.headers.get('Trigger-Source') == 'sidebar-update':
        return render(request, 'portals/admin/students/partials/student_card_right_sidebar.html', context)
    
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

            print('student edited', std_profile)
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
        print(search)
        context = TeacherProfileService.get_paginated_teachers(page_no=page_no, search_query=search)
        return render(request, 'portals/admin/teachers/partials/teachers_table.html', context)
    
    context = AdminTeacherOverviewAggregator.get_teachers_overview(page_no)
    
    return render(request, 'portals/admin/teachers/teachers_directory.html', context)


@login_required
@role_required('ADMIN')
def teacher_detail(request, id):
    context = TeacherProfileService.get_teacher(id)
    print(context)
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
            print(form.errors)
            return HttpResponse('omo something don sup for inside your form or somewhere sha. your from no dey valid. fix up!!')

    else:
        initial = TeacherRegistrationService.get_initial_data(id)
        form = TeacherCreationForm(initial=initial)
    return render(request, 'portals/admin/teachers/partials/create_teacher_modal.html', {'form': form, 'teacher': teacher_profile, 'edit': True, **initial})

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
    print(subjects)

    return render(request, 'portals/admin/teachers/partials/subject_checkboxes.html', {'subjects': subjects, 'selected_subject_ids': request.GET.getlist('selected')})



@login_required
@role_required('ADMIN')
def class_console(request):
    return render(request, 'portals/admin/class_console/class_console.html')

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


