from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from schools.models import School

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "System Super Admin"
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        BURSAR   = "BURSAR", "Bursar"
        STUDENT = "STUDENT", "Student"


    role = models.CharField(max_length=20, choices=Role.choices)
    middle_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], blank=True)

    state_of_origin = models.CharField(max_length=50, blank=True)
    religion = models.CharField(max_length=50, blank=True)
    
    is_onboarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email}) - {self.role}"