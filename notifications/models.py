
from django.conf import settings
from django.db import models

class Notification(models.Model):
    class Priority(models.TextChoices):
        INFO = "INFO", "Information"
        WARNING = "WARNING", "Warning"
        URGENT = "URGENT", "Urgent/Critical"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # URL to redirect to when clicked (e.g., the specific Result page)
    link = models.URLField(max_length=500, blank=True, null=True)
    
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.INFO)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']