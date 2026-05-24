import os
from django.core.management import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "securely provisions the system masteruser superuser for server bootstrapping"

    def handle(self, *args, **kwargs):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'system_root')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not email or not password:
            self.stderr.write(
                "Skipping bootstrap: DJANGO_SUPERUSER_EMAIL or PASSWORD env variables are missing."
            )
            return
        
        if User.objects.filter(email=email).exists() or User.objects.filter(username=username).exists():
            self.stderr.write(self.style.SUCCESS('system superuse already exists. clean skip'))
            return
        
        user = User.objects.create(
            username=username,
            email=email,
            password=password,
            role=User.Role.SUPERADMIN,
            is_onboarded=True
        )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully provisioned system master account: {user.email}")
        )