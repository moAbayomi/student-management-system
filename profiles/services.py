from .models import StudentProfile, TeacherProfile
from academics.models import Subject
from django.contrib.auth import get_user_model
from academics.models import ClassArm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
import secrets

User = get_user_model()


class StudentProfileService:
    @staticmethod
    def get_stats():
        return {
            'latest_students': StudentProfile.objects.order_by('-user_id')[:5],
            'total_students': StudentProfile.objects.all().count()
        }
    
    @staticmethod
    def get_students_queryset():
            return StudentProfile.objects.all().order_by('-user_id')
    
    @staticmethod
    def get_paginated_students(page_no, search_query=None, class_filter=None):
        stds = StudentProfile.objects.all().order_by('-user_id') 

        if search_query:
            stds = stds.filter(Q(user__first_name__icontains=search_query) | Q(user__last_name__icontains=search_query))

        if class_filter and class_filter != 'All Classes':
            stds = stds.filter(class_arm__class_level__name__icontains=class_filter)
        

        paginator = Paginator(stds, 20)
        page_obj = paginator.get_page(page_no)

        return {
             'students': page_obj,
             'total_students': paginator.count
        }
    
    @staticmethod
    def get_student(id):
        student = StudentProfile.objects.get(id=id)
        return {
             'student': student,
             'age': student.date_of_birth
             }

    
    
class TeacherProfileService:
    @staticmethod
    def get_stats():
         return {
              'total_teachers': TeacherProfile.objects.all().count()
         }
    
    @staticmethod
    def get_teachers_queryset():
         return TeacherProfile.objects.all().order_by('-user_id')

    @staticmethod
    def get_paginated_teachers(page_no=1, search_query=None,):
         
         teachers = TeacherProfile.objects.all().order_by('-user_id')
         if search_query:
              teachers = teachers.filter(Q(user__first_name__icontains=search_query) | Q(user__last_name__icontains=search_query))
         
         paginator = Paginator(teachers, 20)

         page_obj = paginator.get_page(page_no)
         return {
              'teachers': page_obj,
              'total_teachers': paginator.count
         }
    
    @staticmethod
    def get_teacher(id):
         return {'teacher' : TeacherProfile.objects.get(id=id)}
         

class StudentRegistrationService:
     @staticmethod
     def generate_temp_password():
          return 'pswdtakbir1234'
     
     @staticmethod
     @transaction.atomic
     def create_draft_student(school, data:dict) -> StudentProfile:
          first_name = data.get('first_name')
          last_name = data.get('last_name')
          gender = data.get('gender')

          base_username = f'{first_name.lower()}{last_name.lower()}'
          suffix = secrets.token_hex(3)
          username = f'{base_username}.{suffix}'

          temp_password = StudentRegistrationService.generate_temp_password()
          user = User.objects.create(
               username=username,
               first_name=first_name,
               gender=gender,
               last_name=last_name,
               role='STUDENT',
          )
          user.set_password(temp_password)
          user.save()

          class_arm_id = data.get('class_arm')
          class_arm_instance = ClassArm.objects.get(id=class_arm_id)

          std = StudentProfile.objects.create(
               user=user,
               school=school,
               admission_number=None,
               class_arm=class_arm_instance,
               date_of_birth=data.get('dob')
          )

          return StudentProfile
     
     @staticmethod
     def create_complete_student(form) -> StudentProfile:
          data = form.clean()
          temp_password = StudentRegistrationService.generate_temp_password()


          base_username = f'{data['first_name'].lower()}{data['last_name'].lower()}'
          suffix = secrets.token_hex(3)
          username = f'{base_username}.{suffix}'

          user = User.objects.create(
          username=username,
          first_name=data.get('first_name', ''),
          middle_name=data.get('middle_name', ''),
          last_name=data.get('last_name', ''),
          gender=data.get('gender', ''),
          role='STUDENT',
          state_of_origin=data.get('state_of_origin', ''),
          religion=data.get('religion', ''),
          address=data.get('address', '')
          )
          user.set_password(temp_password)          # ← fixed: method call, not assignment
          user.save()

          std_profile = StudentProfile.objects.create(
          user=user,
          status='ACTIVE',
          date_of_birth=data.get('dob'),
          admission_number=None,
          admission_type=data.get('admission_type', ''),
          entry_term=data.get('entry_term', ''),
          previous_school=data.get('previous_school', ''),
          previous_class=data.get('previous_class', ''),
          fee_plan=data.get('fee_plan', ''),
          guardian_first_name=data.get('guardian_first_name', ''),
          guardian_last_name=data.get('guardian_last_name', ''),
          guardian_relationship=data.get('guardian_relationship', ''),
          guardian_phone=data.get('guardian_phone', ''),
          guardian_occupation=data.get('guardian_occupation', ''),
          guardian_email=data.get('guardian_email', ''),
          guardian_nin=data.get('guardian_nin', ''),
          guardian_address=data.get('guardian_address', ''),
          emergency_name=data.get('emergency_name', ''),
          emergency_phone=data.get('emergency_phone', ''),
          blood_group=data.get('blood_group', ''),
          genotype=data.get('genotype', ''),
          disability=data.get('disability', ''),
          allergies=data.get('allergies', ''),
          medical_conditions=data.get('medical_conditions', ''),
          admin_notes=data.get('admin_notes', '')
          )

          return std_profile

     @staticmethod
     def edit_draft_student(id, data) -> StudentProfile:
          std = StudentProfile.objects.get(id=id)
          user = std.user
          user.first_name = data.get('first_name')
          user.last_name = data.get('last_name')
          user.gender = data.get('gender')
          user.save()

          std.date_of_birth = data.get('dob')
          std.save()

          return std
     
     @staticmethod
     def get_initial_data(id) -> dict:
          student = StudentProfile.objects.get(id=id)
          return {
               'first_name': student.user.first_name,
               'last_name': student.user.last_name,
               'gender': student.user.gender,
               'dob': student.date_of_birth
          }


     @staticmethod
     def edit_complete_student(id, form) -> StudentProfile:
          data = form.clean()
          student_profile = StudentProfile.objects.get(id=id)
          user = student_profile.user

          user.first_name = data.get('first_name', '')
          user.middle_name = data.get('middle_name', '')
          user.last_name = data.get('last_name', '')
          user.gender = data.get('gender', '')
          user.state_of_origin = data.get('state_of_origin', '')
          user.religion = data.get('religion', '')
          user.address = data.get('address', '')
          # Handle photo upload (if any)
          photo = data.get('photo')      # will be an InMemoryUploadedFile or None
          if photo:
               user.profile_picture.save(photo.name, photo, save=False)
          user.save()

          student_profile.date_of_birth = data.get('dob')
          student_profile.admission_type = data.get('admission_type', '')
          student_profile.entry_term = data.get('entry_term', '')
          student_profile.previous_school = data.get('previous_school', '')
          student_profile.previous_class = data.get('previous_class', '')
          student_profile.fee_plan = data.get('fee_plan', '')
          student_profile.guardian_first_name = data.get('guardian_first_name', '')
          student_profile.guardian_last_name = data.get('guardian_last_name', '')
          student_profile.guardian_relationship = data.get('guardian_relationship', '')
          student_profile.guardian_phone = data.get('guardian_phone', '')
          student_profile.guardian_occupation = data.get('guardian_occupation', '')
          student_profile.guardian_email = data.get('guardian_email', '')
          student_profile.guardian_nin = data.get('guardian_nin', '')
          student_profile.guardian_address = data.get('guardian_address', '')
          student_profile.emergency_name = data.get('emergency_name', '')
          student_profile.emergency_phone = data.get('emergency_phone', '')
          student_profile.blood_group = data.get('blood_group', '')
          student_profile.genotype = data.get('genotype', '')
          student_profile.disability = data.get('disability', '')
          student_profile.allergies = data.get('allergies', '')
          student_profile.medical_conditions = data.get('medical_conditions', '')
          student_profile.admin_notes = data.get('admin_notes', '')

          student_profile.save()

          return student_profile


     

class TeacherRegistrationService:
     @staticmethod
     def generate_temp_password():
          return 'pswdtakbir1234'
     
     
     @staticmethod
     @transaction.atomic
     def create_full_teacher(form) -> TeacherProfile:
          data = form.cleaned_data
          temp_password = 'pswdtakbir1234'

          base_username = f'{data['first_name'].lower()}{data['last_name'].lower()}'
          suffix = secrets.token_hex(3)
          username = f'{base_username}.{suffix}'

          user = User.objects.create(
               username=username,
               first_name=data.get('first_name', ''),
               middle_name=data.get('middle_name', ''),
               last_name=data.get('last_name', ''),
               gender=data.get('gender', ''),
               email=data.get('email', ''),
               phone_number=data.get('phone', ''),
               role='TEACHER',
               state_of_origin=data.get('state_of_origin', ''),
               religion=data.get('religion', ''),
               address=data.get('address', '')
          )
          user.set_password(temp_password)
          user.save()

          teacher_profile = TeacherProfile.objects.create(
               user=user,
               status='ACTIVE',
               date_of_birth=data.get('dob'),
               qualification=data.get('qualification'),
               years_of_exp=data.get('years_of_exp'),
               department=data.get('department'),
               max_weekly_hours=data.get('max_weekly_hours'),
          )
          if data.get('subjects'):
               teacher_profile.subjects.set(data.get('subjects'))
          teacher_profile.save()
          return teacher_profile

     @staticmethod
     @transaction.atomic
     def edit_complete_student(id, form) -> TeacherProfile:
          data = form.cleaned_data
          teacher_profile = TeacherProfile.objects.get(id=id)

          user = teacher_profile.user

          user_fields = ['first_name', 'last_name', 'middle_name', 'email', 'gender',
                   'religion', 'state_of_origin', 'address', 'phone_number']
          
          for field in user_fields:
               if field in data:
                    setattr(user, field, data[field])
          
          photo = data.get('photo', '')
          if photo:
               user.profile_picture.save(photo.name, photo, save=False)

          user.save()

          profile_fields = ['date_of_birth', 'qualification', 'years_of_exp',
                      'department', 'max_weekly_hours']
          
          for field in profile_fields:
               if field in data:
                    setattr(teacher_profile, field, data[field])
               
          if 'dob' in data:
               teacher_profile.date_of_birth = data['dob']

          teacher_profile.save()

          if data.get('subjects'):
               teacher_profile.subjects.set(data.get('subjects'))


          return teacher_profile
     
     @staticmethod
     def get_initial_data(id) -> dict:
          teacher_profile = TeacherProfile.objects.get(id=id)
          departments = TeacherProfile.Department.choices

          dept_query = {
        'JUNIOR': ['JNR_CORE', 'JUNIOR'],
        'SCIENCE': ['SNR_CORE', 'SCIENCE', 'VOCATIONAL_TRADE'],
        'ARTS_HUMANITIES': ['SNR_CORE', 'ARTS', 'VOCATIONAL_TRADE'],
        'COMMERCIAL': ['SNR_CORE', 'COMMERCIAL', 'VOCATIONAL_TRADE'],
        'VOCATIONAL_TRADE': ['SNR_CORE', 'VOCATIONAL_TRADE']
          }
          if teacher_profile.department:
               subjects = Subject.objects.filter(category__in=dept_query[teacher_profile.department])
          else:
               subjects = Subject.objects.all()

          return {
               'departments': departments,
               'subjects': subjects
          }
          











