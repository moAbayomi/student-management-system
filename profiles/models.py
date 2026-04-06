from django.db import models
from users.models import User
from schools.models import School
from academics.models import Subject, ClassArm

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject, blank=True)
    class_arms = models.ManyToManyField(ClassArm, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    date_joined = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject, blank=True, related_name='students')
    class_arm = models.ForeignKey(ClassArm, on_delete=models.CASCADE)
    admission_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.get_full_name()}"