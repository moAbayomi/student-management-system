from profiles.models import StudentProfile
from academics.models import SubjectAssignment
from schools.models import AcademicSession
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'load each students with subjects corresponding to their class arm'

    def handle(self, *args, **kwargs):

        session = AcademicSession.objects.get(is_current=True)

        for student in StudentProfile.objects.all():
            assignments = SubjectAssignment.objects.filter(class_arm=student.class_arm, session=session)

            subjects_to_add = [a.subject for a in assignments]
            student.subjects.set(subjects_to_add)

