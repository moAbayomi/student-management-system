from django.contrib.auth.models import AbstractUser
from django.db import models
from schools.models import School

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        BURSAR   = "BURSAR", "Bursar"
        STUDENT = "STUDENT", "Student"

    base_role = Role.ADMIN

    role = models.CharField(max_length=50, choices=Role.choices)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    default=Role.ADMIN
    
    def save(self, *args, **kwargs):
        if not self.role: # Only set a default if NO role was provided
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)