from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from colorfield.fields import ColorField


class School(models.Model):
    # Identity
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=300, blank=True)
    about = models.TextField(blank=True)

    # Branding
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='school_favicons/', blank=True, null=True)
    hero_image = models.ImageField(upload_to='school_heroes/', blank=True, null=True)
    primary_color = ColorField(default='#007bff')
    secondary_color = ColorField(default='#6c757d')

    # Contact
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Leadership
    principal_name = models.CharField(max_length=200, blank=True)
    principal_message = models.TextField(blank=True)
    principal_photo = models.ImageField(
        upload_to='principal_photos/', blank=True, null=True
    )

    # Feature flags — toggle per school
    has_payments = models.BooleanField(default=True)
    has_whatsapp = models.BooleanField(default=False)
    has_attendance = models.BooleanField(default=True)
    has_results_pin = models.BooleanField(default=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)

    # operational
    timezone = models.CharField(max_length=50, default='Africa/Lagos')

    # system preferences
    grading_system = models.CharField(
        max_length=20,
        choices = [('PERCENTAGE', 'Percentage (0-100)'), ('GPA', 'GPA (4.0/5.0)')],
        default='PERCENTAGE'
    )
    pass_mark = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)

    def __str__(self):
        return self.name

    # This project runs ONE school per deployment. The School row is the
    # school's settings record, so we refuse to create a second one.
    def clean(self):
        if not self.pk and School.objects.exists():
            raise ValidationError("A school already exists. Edit it instead of creating a new one.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class AcademicSession(models.Model):

    class SessionStatus(models.TextChoices):
        PLANNING = "PLANNING", "Planning/Admission"
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    name = models.CharField(
        max_length=10,
        unique=True,
        help_text="e.g. 2025/2026"
    )
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=10, 
        choices=SessionStatus.choices, 
        default=SessionStatus.PLANNING
    )

    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_year']

    def save(self, *args, **kwargs):
        # Only one session can be current at a time
        if self.is_current:
            AcademicSession.objects.filter(
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def create_default_terms(self):
        """Create First, Second, Third Term for this session.
        Dates are left blank — admin fills them in later on the Term edit page."""
        for term_type, sequence in [
            (AcademicTerm.TermChoices.FIRST, 1),
            (AcademicTerm.TermChoices.SECOND, 2),
            (AcademicTerm.TermChoices.THIRD, 3),
        ]:
            AcademicTerm.objects.get_or_create(
                session=self,
                term_type=term_type,
                defaults={'sequence': sequence},
            )
    
    
    def make_current(self):
        """Mark this session ACTIVE and current, and its First Term current."""
        with transaction.atomic():
            # Archive the session that was running. Sessions still in
            # PLANNING (e.g. next year being prepared) are left alone.
            AcademicSession.objects.exclude(pk=self.pk).filter(
                status=AcademicSession.SessionStatus.ACTIVE,
            ).update(status=AcademicSession.SessionStatus.ARCHIVED)
            AcademicSession.objects.exclude(pk=self.pk).update(is_current=False)
            AcademicTerm.objects.update(is_current=False)
    
            self.is_current = True
            self.status = AcademicSession.SessionStatus.ACTIVE
            self.save(update_fields=['is_current', 'status'])
    
            first_term = self.terms.order_by('sequence').first()
            if first_term:
                first_term.is_current = True
                first_term.save(update_fields=['is_current'])


class AcademicTerm(models.Model):
    class TermChoices(models.TextChoices):
        FIRST = "FIRST", "First Term"
        SECOND = "SECOND", "Second Term"
        THIRD = "THIRD", "Third Term"

    session = models.ForeignKey(
        'schools.AcademicSession',
        on_delete=models.CASCADE,
        related_name='terms'
    )
    term_type = models.CharField(
        max_length=10,
        choices=TermChoices.choices
    )

    sequence = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text = "1 for First, 2 for Second, etc. Helps with trend graphs"
    )

    # deadlines (Production guard rails)
    grading_deadline = models.DateTimeField(null=True, blank=True, help_text="After this date, teachers cannot edit marks without Admin override.")
    next_term_begins = models.DateField(null=True, blank=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    result_published = models.BooleanField(default=False)



    class Meta:
        # A session can't have two of the same term type
        unique_together = ('session', 'term_type')

    def save(self, *args, **kwargs):
        # Only one term can be current at a time
        if self.is_current:
            AcademicTerm.objects.filter(
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_term_type_display()} — {self.session.name}"

    def make_current(self):
        """Make this term current. If its session isn't current yet, switch that too."""
        with transaction.atomic():
            if not self.session.is_current:
                # make_current() also marks the session's First Term current
                self.session.make_current()
            self.is_current = True
            self.save(update_fields=['is_current'])  # save() unsets the other current term
    
class ActivityLog(models.Model):
    class Category(models.TextChoices):
        ACADEMIC = "ACADEMIC", "Academic (Grades/Attendance)"
        FINANCE = "FINANCE", "Finance (Fees/Payments)"
        USER = "USER", "User Management (Enrollment/Profiles)"
        SYSTEM = "SYSTEM", "System (Settings/Announcements)"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='activities'
    )
    action = models.CharField(max_length=255) # e.g., "Updated Maths results for SS2A"
    category = models.CharField(
        max_length=20, 
        choices=Category.choices, 
        default=Category.SYSTEM
    )
    
    # Metadata for the "Timeline" view
    description = models.TextField(blank=True, help_text="Extra details or reasons for the action")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Activity Logs"

    def __str__(self):
        return f"{self.actor} - {self.action} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
    

class Announcement(models.Model):
    class TargetAudience(models.TextChoices):
        ALL = "ALL", "Everyone"
        TEACHERS = "TEACHERS", "Teachers Only"
        STUDENTS = "STUDENTS", "Students & Parents"
        ADMINS = "ADMINS", "Admins Only"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    # Targeting & Visibility
    audience = models.CharField(
        max_length=15, 
        choices=TargetAudience.choices, 
        default=TargetAudience.ALL
    )
    
    # Production Features
    is_pinned = models.BooleanField(
        default=False, 
        help_text="Pinned announcements stay at the top of the feed."
    )
    is_active = models.BooleanField(default=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiry_date = models.DateField(
        null=True, 
        blank=True, 
        help_text="Announcement will be hidden after this date."
    )

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title