from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.

class CustomUserAdmin(UserAdmin):
    # This adds your new fields to the 'Personal Info' section in the Admin
    fieldsets = UserAdmin.fieldsets + (
        ('School Specific Data', {'fields': ('role', 'school', 'phone_number', 'address')}),
    )
    
    # This ensures the fields show up when YOU are creating a new user
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('School Specific Data', {'fields': ('role', 'school', 'phone_number', 'address')}),
    )

    # This controls what you see in the "List View" (the table of all users)
    list_display = ['username', 'email', 'role', 'school', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser']

admin.site.register(User, CustomUserAdmin)
