from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Class(models.Model):

    class Level(models.TextChoices):
        JSS1 = 'JSS1', 'JSS 1'
        JSS2 = 'JSS2', 'JSS 2'
        JSS3 = 'JSS3', 'JSS 3'
        SSS1 = 'SSS1', 'SSS 1'
        SSS2 = 'SSS2', 'SSS 2'
        SSS3 = 'SSS3', 'SSS 3'

    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=20, choices=Level.choices)
    order = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.get_name_display()

class ClassArm(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    class_level = models.ForeignKey('Class', on_delete=models.CASCADE)
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
        ('CORE', 'General Core'),
        ('JUNIOR', 'Junior Secondary'),
        ('SCIENCE', 'Senior Science'),
        ('ARTS', 'Senior Arts'),
        ('COMMERCIAL', 'Senior Commercial'),
    ]

    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='CORE')

    def __str__(self):
        return f"{self.name}"
    
    

class SubjectAssignment(models.Model):
    class_arm = models.ForeignKey('ClassArm', on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    session = models.ForeignKey('schools.AcademicSession', on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'TEACHER'}
    )

    class Meta:
        unique_together = ('class_arm', 'subject', 'session')

    def __str__(self):
        return f"{self.subject.name} — {self.class_arm}"
    
class Result(models.Model):
    student = models.ForeignKey('profiles.StudentProfile', on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    session = models.ForeignKey('schools.AcademicSession', on_delete=models.CASCADE)
    term = models.ForeignKey('schools.AcademicTerm', on_delete=models.CASCADE)

    ca_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(40)])   
    exam_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(60)]) 
    total_score = models.FloatField(editable=False, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    
    grade = models.CharField(max_length=2, blank=True)
    remark = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('student', 'subject', 'session', 'term')

    def save(self, *args, **kwargs):
        self.total_score = (self.ca_score or 0) + (self.exam_score or 0)

        if self.total_score > 100:
            raise ValueError("Total score cannot exceed 100.")
        # A1 (75–100), B2 (70–74), B3 (65–69), C4 (60–64), C5 55–59), C6 (50–54), D7 (45–49), E8 (40–44), F9 (0–39)
        if self.total_score >= 75:
            self.grade, self.remark = 'A1', 'Excellent'
        elif self.total_score >= 70:
            self.grade, self.remark = 'B2', 'Very Good'
        elif self.total_score >= 65:
            self.grade, self.remark = 'B3', 'Good'
        elif self.total_score >= 60:
            self.grade, self.remark = 'C4', 'Upper Credit'
        elif self.total_score >= 55:
            self.grade, self.remark = 'C5', 'Credit'
        elif self.total_score >= 50:
            self.grade, self.remark = 'C6', 'Lower Credit'
        elif self.total_score >= 45:
            self.grade, self.remark = 'D7', 'Pass'
        elif self.total_score >= 40:
            self.grade, self.remark = 'E8', 'Weak Pass'
        else:
            self.grade, self.remark = 'F9', 'Fail'
        super().save(*args, **kwargs)

    