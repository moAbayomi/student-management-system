from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.template import Context, Template
from django.test import RequestFactory, TestCase

from .context_processors import school as school_context
from .models import School, AcademicSession, AcademicTerm
from .services import get_school, get_current_session, get_current_term


def make_school(name="Test College"):
    return School.objects.create(name=name, slug="test-college", address="1 School Road")


class SingleSchoolTests(TestCase):
    def test_get_school_returns_none_before_setup(self):
        self.assertIsNone(get_school())

    def test_get_school_returns_the_school(self):
        school = make_school()
        self.assertEqual(get_school(), school)

    def test_cannot_create_a_second_school(self):
        make_school()
        with self.assertRaises(ValidationError):
            School.objects.create(name="Another", slug="another", address="x")

    def test_editing_the_school_still_works(self):
        school = make_school()
        school.name = "Renamed College"
        school.save()
        self.assertEqual(get_school().name, "Renamed College")

    def test_context_processor_exposes_school_to_templates(self):
        make_school()
        context = school_context(RequestFactory().get('/'))
        rendered = Template("{{ school.name }}").render(Context(context))
        self.assertEqual(rendered, "Test College")

    def test_context_processor_is_safe_when_no_school(self):
        context = school_context(RequestFactory().get('/'))
        rendered = Template("{% if school %}yes{% else %}no{% endif %}").render(Context(context))
        self.assertEqual(rendered, "no")


class CurrentSessionAndTermTests(TestCase):
    def test_helpers_return_none_when_nothing_is_current(self):
        self.assertIsNone(get_current_session())
        self.assertIsNone(get_current_term())

    def test_only_one_session_is_current(self):
        old = AcademicSession.objects.create(name="2025/2026", start_year=2025, end_year=2026, is_current=True)
        new = AcademicSession.objects.create(name="2026/2027", start_year=2026, end_year=2027, is_current=True)
        old.refresh_from_db()
        self.assertFalse(old.is_current)
        self.assertEqual(get_current_session(), new)

    def test_only_one_term_is_current(self):
        session = AcademicSession.objects.create(name="2026/2027", start_year=2026, end_year=2027)
        first = AcademicTerm.objects.create(session=session, term_type="FIRST", is_current=True)
        second = AcademicTerm.objects.create(session=session, term_type="SECOND", is_current=True)
        first.refresh_from_db()
        self.assertFalse(first.is_current)
        self.assertEqual(get_current_term(), second)


class SetupSchoolCommandTests(TestCase):
    def test_creates_school_session_and_terms(self):
        call_command('setup_school', name="Test College", session="2026/2027", stdout=_Null(), stderr=_Null())
        self.assertEqual(get_school().name, "Test College")
        self.assertEqual(get_current_session().name, "2026/2027")
        self.assertEqual(AcademicTerm.objects.count(), 3)
        self.assertEqual(get_current_term().term_type, "FIRST")

    def test_running_twice_does_not_duplicate(self):
        for _ in range(2):
            call_command('setup_school', name="Test College", session="2026/2027", stdout=_Null(), stderr=_Null())
        self.assertEqual(School.objects.count(), 1)
        self.assertEqual(AcademicSession.objects.count(), 1)
        self.assertEqual(AcademicTerm.objects.count(), 3)


class _Null:
    def write(self, *args, **kwargs):
        pass
