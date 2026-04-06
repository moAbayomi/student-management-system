from django.core.management.base import BaseCommand
from academics.models import Class, ClassArm, Subject, SubjectAssignment, AcademicSession


# Which subject categories belong to which class level type
JUNIOR_CATEGORIES = ['JNR_CORE', 'JUNIOR']
SENIOR_CATEGORIES = ['SNR_CORE']  # core only — science/arts/commercial added separately


def is_junior(class_name):
    return class_name.upper().startswith('JSS')


class Command(BaseCommand):
    help = 'Auto-assigns core subjects to all class arms for the current session'

    def handle(self, *args, **kwargs):
        session = AcademicSession.objects.filter(is_current=True).first()
        if not session:
            self.stdout.write(self.style.ERROR('No current session found. Set is_current=True on a session first.'))
            return

        arms = ClassArm.objects.select_related('class_level').all()
        if not arms.exists():
            self.stdout.write(self.style.ERROR('No class arms found. Create arms first.'))
            return

        created_count = 0
        skipped_count = 0

        for arm in arms:
            level_name = arm.class_level.name

            if is_junior(level_name):
                categories = JUNIOR_CATEGORIES
            else:
                categories = SENIOR_CATEGORIES

            subjects = Subject.objects.filter(category__in=categories)

            for subject in subjects:
                obj, created = SubjectAssignment.objects.get_or_create(
                    class_arm=arm,
                    subject=subject,
                    session=session,
                    defaults={'teacher': None}
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. {created_count} assignments created, {skipped_count} already existed.'
        ))