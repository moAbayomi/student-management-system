from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError

class Class(models.Model):

    class Level(models.TextChoices):
        JSS1 = 'JSS1', 'JSS 1'
        JSS2 = 'JSS2', 'JSS 2'
        JSS3 = 'JSS3', 'JSS 3'
        SSS1 = 'SSS1', 'SSS 1'
        SSS2 = 'SSS2', 'SSS 2'
        SSS3 = 'SSS3', 'SSS 3'

    name = models.CharField(max_length=20, choices=Level.choices)
    order = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.get_name_display()

class ClassArm(models.Model):
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)
    class_teacher = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_teacher_of',
        limit_choices_to={'role': 'TEACHER'}
    )
    subjects = models.ManyToManyField('Subject', related_name='arms')

    def __str__(self):
        return f"{self.class_level.name}{self.name}"  
    
class Subject(models.Model):

    CATEGORY_CHOICES = [
        ('JNR_CORE', 'Junior Core'),
        ('SNR_CORE', 'Senior Core'),
        ('JUNIOR', 'Junior Secondary'),
        ('SCIENCE', 'Senior Science'),
        ('ARTS', 'Senior Arts'),
        ('COMMERCIAL', 'Senior Commercial'),
        ('VOCATIONAL_TRADE', 'Vocational Trade')
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='CORE')

    class Meta:
        unique_together = ('name', 'code')

    def __str__(self):
        return f"{self.name}"
    
    

class SubjectAssignment(models.Model):
    class_arm = models.ForeignKey(ClassArm, on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    session = models.ForeignKey('schools.AcademicSession', on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        'profiles.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True, 
        related_name='assignments'
    )

    class Meta:
        unique_together = ('class_arm', 'subject', 'session')

    def __str__(self):
        return f"{self.subject.name} — {self.class_arm}"
    
class Result(models.Model):
    student = models.ForeignKey('profiles.StudentProfile', on_delete=models.CASCADE, related_name='student')
    subject_assignment = models.ForeignKey(SubjectAssignment, on_delete=models.CASCADE, related_name='results')
    term = models.ForeignKey('schools.AcademicTerm', on_delete=models.CASCADE)
 
    total_score = models.FloatField(editable=False, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    grade = models.CharField(max_length=2, blank=True)
    remark = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('student', 'subject_assignment', 'term')
    
    def clean(self):
        if (self.total_score or 0) > 100:
            raise ValidationError('Total must not be more than 100')

class GradeComponent(models.Model):
    name = models.CharField(max_length=50)
    max_score = models.FloatField()
    is_exam = models.BooleanField(default=False)

class ResultEntry(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='entries')
    component = models.ForeignKey(GradeComponent, on_delete=models.CASCADE)
    score = models.FloatField(default=0)

    def clean(self):
        if self.score > self.component.max_score:
            raise ValidationError(
                f"Score {self.score} exceeds maximum allowed ({self.component.max_score}) for {self.component.name}"
            )
        
    class Meta:
        unique_together = ('result', 'component')

class ReportCard(models.Model):
    # Core Links
    student = models.ForeignKey('profiles.StudentProfile', on_delete=models.CASCADE, related_name='report_cards')
    term = models.ForeignKey('schools.AcademicTerm', on_delete=models.CASCADE)
    class_arm = models.ForeignKey('academics.ClassArm', on_delete=models.CASCADE)
    
    # Aggregated Academic Stats
    total_obtained = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    total_attainable = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    position = models.PositiveIntegerField(null=True, blank=True)
    
    # Attendance Summary (Auto-calculated from DailyAttendance)
    days_present = models.PositiveIntegerField(default=0)
    days_absent = models.PositiveIntegerField(default=0)
    days_school_opened = models.PositiveIntegerField(default=0)

    # Comments (The "Principal's Office" section)
    form_teacher_comment = models.TextField(blank=True)
    principal_comment = models.TextField(blank=True)
    
    # Nigerian Standard: Affective & Psychomotor Domains (1-5 Scale)
    # You can move these to a separate model if the school has 20+ traits,
    # but for a standard school, these columns work best.
    punctuality = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    neatness = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    honesty = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    self_control = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    handwriting = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    sports = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])

    # Status
    is_locked = models.BooleanField(default=False, help_text="Once locked, grades cannot be changed.")
    
    class Meta:
        unique_together = ('student', 'term')
        ordering = ['-average'] # Automatically ranks them by average

    def __str__(self):
        return f"Report Card: {self.student.user.get_full_name()} - {self.term}"
        
class DailyAttendance(models.Model):

    PRESENT = 'P'
    ABSENT = 'A'
    EXCUSED = 'E'
    LATE = 'L'

    STATUS_CHOICES = [
        (PRESENT, 'Present'),
        (ABSENT, 'Absent'),
        (EXCUSED, 'Excused'),
        (LATE, 'Late')
    ]

    student = models.ForeignKey('profiles.StudentProfile', on_delete=models.CASCADE, related_name='attendance_records')
    class_arm = models.ForeignKey('academics.ClassArm', on_delete=models.CASCADE)
    date = models.DateField()
    term = models.ForeignKey('schools.AcademicTerm', on_delete=models.CASCADE)

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PRESENT)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    updated_by = models.ForeignKey(
    settings.AUTH_USER_MODEL, 
    on_delete=models.SET_NULL, 
    null=True, 
    blank=True
)
    

    class Meta:
        unique_together = ('student', 'date')
        verbose_name_plural = 'Daily Attendance'

    def __str__(self):
        return f'{self.student.user.get_full_name()} - {self.date}'
    

class Period(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_academic = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_time']
    

class TimeTableSlot(models.Model):
    class DayChoices(models.TextChoices):
        MONDAY = "MON", "Monday"
        TUESDAY = "TUE", "Tuesday"
        WEDNESDAY = "WED", "Wednesday"
        THURSDAY = "THU", "Thursday"
        FRIDAY = "FRI", "Friday"
        SATURDAY = "SAT", "Saturday"
    
    day = models.CharField(max_length=3, choices=DayChoices.choices)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    class_arm = models.ForeignKey(ClassArm, on_delete=models.CASCADE)
    subject_assignment = models.ForeignKey(SubjectAssignment, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('day', 'period', 'class_arm')
    


    

    