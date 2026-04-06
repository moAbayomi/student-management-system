from django.db import models
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

    def __str__(self):
        return self.name


class AcademicSession(models.Model):
    school = models.ForeignKey(             # ← the fix
        School,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    name = models.CharField(
        max_length=10,
        help_text="e.g. 2025/2026"
    )
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_year']
        # A school can't have two sessions with the same name
        unique_together = ('school', 'name')

    def save(self, *args, **kwargs):
        # If this is being set as current, unset all others for this school
        if self.is_current:
            AcademicSession.objects.filter(
                school=self.school,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class AcademicTerm(models.Model):
    class TermChoices(models.TextChoices):
        FIRST = "FIRST", "First Term"
        SECOND = "SECOND", "Second Term"
        THIRD = "THIRD", "Third Term"

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name='terms'
    )
    term_type = models.CharField(
        max_length=10,
        choices=TermChoices.choices
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        # A session can't have two of the same term type
        unique_together = ('session', 'term_type')

    def save(self, *args, **kwargs):
        # If this term is current, unset all others in the same school's sessions
        if self.is_current:
            AcademicTerm.objects.filter(
                session__school=self.session.school,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_term_type_display()} — {self.session.name}"