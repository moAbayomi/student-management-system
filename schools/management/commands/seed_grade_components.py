from django.core.management.base import BaseCommand

from schools.models import GradeComponent


class Command(BaseCommand):
    help = "Seed default grade components (CA1=20, CA2=20, Exam=60)."

    def handle(self, *args, **options):
        defaults = [
            ("CA1", 20.0, False),
            ("CA2", 20.0, False),
            ("Exam", 60.0, True),
        ]
        for name, score, is_exam in defaults:
            obj, created = GradeComponent.objects.update_or_create(
                name=name,
                defaults={"max_score": score, "is_exam": is_exam},
            )
            self.stdout.write(
                f"{'Created' if created else 'Updated'} {obj.name} ({obj.max_score})"
            )
        self.stdout.write(self.style.SUCCESS("Done."))
