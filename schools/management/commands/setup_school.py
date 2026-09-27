import os

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from schools.models import School, AcademicSession, AcademicTerm


class Command(BaseCommand):
    help = (
        "Creates the school record and (optionally) the current session with its 3 terms. "
        "Safe to run more than once: anything that already exists is left alone."
    )

    def add_arguments(self, parser):
        parser.add_argument('--name', default=os.environ.get('SCHOOL_NAME'))
        parser.add_argument('--address', default=os.environ.get('SCHOOL_ADDRESS', ''))
        parser.add_argument(
            '--session',
            default=os.environ.get('SCHOOL_SESSION'),
            help='e.g. 2026/2027. Creates the session + First/Second/Third terms and marks it current.',
        )

    def handle(self, *args, **options):
        school = School.objects.first()
        if school:
            self.stdout.write(f"School already set up: {school.name}. Skipping.")
        elif not options['name']:
            self.stderr.write("No school yet. Pass --name (or set SCHOOL_NAME) to create one.")
            return
        else:
            school = School.objects.create(
                name=options['name'],
                slug=slugify(options['name']),
                address=options['address'],
            )
            self.stdout.write(self.style.SUCCESS(f"Created school: {school.name}"))

        if options['session']:
            self._setup_session(options['session'])

    def _setup_session(self, name):
        try:
            start_year, end_year = (int(y) for y in name.split('/'))
        except ValueError:
            self.stderr.write(f"Invalid session '{name}'. Use the format 2026/2027.")
            return

        session, created = AcademicSession.objects.get_or_create(
            name=name,
            defaults={
                'start_year': start_year,
                'end_year': end_year,
                'status': AcademicSession.SessionStatus.ACTIVE,
            },
        )
        if not created:
            self.stdout.write(f"Session {name} already exists. Skipping.")
            return

        session.is_current = True
        session.save()

        for sequence, term_type in enumerate(AcademicTerm.TermChoices.values, start=1):
            AcademicTerm.objects.create(
                session=session,
                term_type=term_type,
                sequence=sequence,
                is_current=(sequence == 1),
            )
        self.stdout.write(self.style.SUCCESS(
            f"Created session {name} with 3 terms. First Term is current."
        ))
