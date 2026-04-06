from django.db import models
from schools.models import School, AcademicSession

class Class(models.Model):

    class Level(models.TextChoices):
        JSS1 = 'JSS1', 'JSS 1'
        JSS2 = 'JSS2', 'JSS 2'
        JSS3 = 'JSS3', 'JSS 3'
        SSS1 = 'SSS1', 'SSS 1'
        SSS2 = 'SSS2', 'SSS 2'
        SSS3 = 'SSS3', 'SSS 3'

    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, choices=Level.choices)
    order = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.get_name_display()

class ClassArm(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
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
        return f"{self.class_level.name}{self.name}"  # JSS1A
    
class Subject(models.Model):

    CATEGORY_CHOICES = [
        ('CORE', 'General Core'),
        ('JUNIOR', 'Junior Secondary'),
        ('SCIENCE', 'Senior Science'),
        ('ARTS', 'Senior Arts'),
        ('COMMERCIAL', 'Senior Commercial'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='CORE')

    def __str__(self):
        return f"{self.name}"
    

class SubjectAssignment(models.Model):
    class_arm = models.ForeignKey(ClassArm, on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
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