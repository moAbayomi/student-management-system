from django.db import models
from datetime import date
from django.utils import timezone
from academics.models import Subject

from django.db import models

class TeacherProfile(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
        ACTIVE = "ACTIVE", "Active"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        RESIGNED = "RESIGNED", "Resigned"
        TERMINATED = "TERMINATED", "Terminated"

    class Department(models.TextChoices):
        JUNIOR           = "JUNIOR", "Junior Secondary (General)"
        SCIENCE          = "SCIENCE", "Senior Secondary - Sciences"
        ARTS_HUMANITIES  = "ARTS_HUMANITIES", "Senior Secondary - Arts & Humanities"
        COMMERCIAL       = "COMMERCIAL", "Senior Secondary - Commercial"
        VOCATIONAL_TRADE = "VOCATIONAL_TRADE", "Senior Secondary - Vocational & Trades"

    # ── Core relationships ──
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='teacher_profile')

    # ── Status & onboarding ──
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    onboarding_token = models.UUIDField(null=True, blank=True, unique=True)
    onboarding_token_expires_at=models.DateTimeField(auto_now=True)

    # ── Professional info ──
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    qualification = models.CharField(
        max_length=50,
        choices=[
            ('B.Ed', 'B.Ed'), ('B.Sc', 'B.Sc'), ('B.A', 'B.A'),
            ('B.Tech', 'B.Tech'), ('M.Sc', 'M.Sc'), ('M.A', 'M.A'),
            ('M.Ed', 'M.Ed'), ('PGDE', 'PGDE'), ('Ph.D', 'Ph.D'),
            ('NCE', 'NCE'), ('Other', 'Other')
        ],
        blank=True, null=True
    )
    years_of_exp = models.PositiveIntegerField(null=True, blank=True)
    date_joined = models.DateField(null=True, blank=True)

    # ── School‑level classification ──
    department = models.CharField(
        max_length=20, 
        choices=Department.choices, 
        default=Department.JUNIOR
    )
    # ── Teaching load ──
    subjects = models.ManyToManyField('academics.Subject', blank=True, related_name='teachers')
    max_weekly_hours = models.PositiveSmallIntegerField(default=30)

    # ── Form teacher assignment ──
    assigned_class_arm = models.ForeignKey(
        'academics.ClassArm',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='form_teachers'
    )

    # ── Additional roles ──
    roles = models.ManyToManyField('TeacherRole', blank=True, related_name='teachers')

    # ── Permissions ──
    can_login_portal = models.BooleanField(default=True)
    can_upload_results = models.BooleanField(default=True)
    can_mark_attendance = models.BooleanField(default=True)
    can_post_announcements = models.BooleanField(default=False)

    # ── Metadata ──
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id or 'No ID'})"
    

class StudentProfile(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
        ACTIVE = "ACTIVE", "Active"
        GRADUATED = "GRADUATED", "Graduated"
        SUSPENDED = "SUSPENDED", "Suspended"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
        INACTIVE = "INACTIVE", "Inactive"

    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='student_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=15, 
        choices=Status.choices, 
        default=Status.PENDING_REVIEW
    )
    subjects = models.ManyToManyField(Subject, blank=True, related_name='students')
    admission_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    onboarding_token = models.UUIDField(null=True, blank=True, unique=True)
    onboarding_token_expires_at= models.DateTimeField(auto_now=True)
    class_arm = models.ForeignKey(
        'academics.ClassArm', 
        on_delete=models.PROTECT, # Protect prevents deleting an arm if students are in it
        related_name='students',
        null=True,
        blank=True
    )

    # Academic Tracking Form additions
    admission_type = models.CharField(max_length=50, blank=True)
    entry_term = models.CharField(max_length=50, blank=True)
    previous_school = models.CharField(max_length=255, blank=True)
    previous_class = models.CharField(max_length=50, blank=True)
    fee_plan = models.CharField(max_length=50, blank=True)


    # Primary Guardian Data
    guardian_first_name = models.CharField(max_length=100, blank=True)
    guardian_last_name = models.CharField(max_length=100, blank=True)
    guardian_relationship = models.CharField(max_length=50, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_email = models.EmailField(blank=True)
    guardian_occupation = models.CharField(max_length=100, blank=True)
    guardian_nin = models.CharField(max_length=50, blank=True)
    guardian_address = models.TextField(blank=True)

    # Emergency Contact Details
    emergency_name = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Medical Records
    blood_group = models.CharField(max_length=5, blank=True)
    genotype = models.CharField(max_length=5, blank=True)
    disability = models.CharField(max_length=100, blank=True)
    allergies = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    
    # System Admin Notes
    admin_notes = models.TextField(blank=True)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        
        today = date.today()

        has_had_birthday = (today.day, today.month) >= (self.date_of_birth.day, self.date_of_birth.month)

        return today.year - self.date_of_birth.year - (0 if has_had_birthday else 1)



    def __str__(self):
        return f"{self.user.get_full_name()}"
    

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs) 
        if is_new and self.class_arm:
            arm_subjects = self.class_arm.subjects.all()
            if arm_subjects.exists():
                self.subjects.set(arm_subjects)



class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    class_arm = models.ForeignKey('academics.ClassArm', on_delete=models.CASCADE)
    session = models.ForeignKey('schools.AcademicSession', on_delete=models.CASCADE)
    
    # Nigerian Context: We often track if a student is 'Promoted', 'Repeating', or 'Withdrawn'
    class EnrollmentStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PROMOTED = "PROMOTED", "Promoted"
        REPEATING = "REPEATING", "Repeating"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    status = models.CharField(max_length=15, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE)
    date_enrolled = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'session') 


class TeacherRole(models.Model):

    #Form Teacher
    #Head of Department (HOD)
    #Deputy HOD
    #Bursar
    #Discipline Master
    #Guidance Counsellor
    #Exam Officer
    #Sports Master
    name = models.CharField(max_length=50, unique=True)
    desc = models.TextField(null=True, blank=True)