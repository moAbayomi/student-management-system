import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from academics.models import ClassArm
from schools.models import School
from profiles.models import StudentProfile


User = get_user_model()

class Command(BaseCommand):
    help = 'seed the db with test students'

    def handle(self, *args, **kwargs):
        school = School.objects.first()
        arms = ClassArm.objects.all()

        test_password = 'Studentpass123'
        student_count = 0
        for arm in arms:
            arm_prefix = f"{arm.class_level.name}{arm.name}_"
            for i in range(25):
                unique_suffix = f"{arm_prefix}{i}"
                username = f"student_{unique_suffix}".lower()

                if not User.objects.filter(username=username).exists():
                    user = User.objects.create(
                        username=username,
                        first_name=f"first_{unique_suffix}",
                        last_name=f"last_{unique_suffix}",
                        role='STUDENT'
                    )

                    user.set_password(test_password)
                    user.save()

                    StudentProfile.objects.create(
                        user=user,
                        school=school,
                        class_arm=arm,
                        admission_number=f"ADM/{arm_prefix}/{2026}/{i:03d}"
                    )
                    student_count += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully created {student_count} students with password: {test_password}'))