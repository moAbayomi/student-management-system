import json
from datetime import date, timedelta

from django.test import TestCase

from academics.models import Class, ClassArm, DailyAttendance, Subject, SubjectAssignment
from profiles.models import StudentProfile, TeacherProfile
from schools.models import AcademicSession, AcademicTerm
from users.models import User


def make_user(username, role):
    return User.objects.create_user(username=username, password='pass', role=role,
                                    first_name=username.title(), last_name='Test')


class PortalTestCase(TestCase):
    """Two arms, each with its own form teacher and one student."""

    @classmethod
    def setUpTestData(cls):
        cls.session = AcademicSession.objects.create(name='2026/2027', start_year=2026, end_year=2027, is_current=True)
        cls.term = AcademicTerm.objects.create(session=cls.session, term_type='FIRST', sequence=1, is_current=True)
        level = Class.objects.create(name='JSS1', order=1)

        cls.admin = make_user('admin', 'ADMIN')
        cls.teacher_a = TeacherProfile.objects.create(user=make_user('teacher_a', 'TEACHER'))
        cls.teacher_b = TeacherProfile.objects.create(user=make_user('teacher_b', 'TEACHER'))
        cls.arm_a = ClassArm.objects.create(class_level=level, name='A', class_teacher=cls.teacher_a)
        cls.arm_b = ClassArm.objects.create(class_level=level, name='B', class_teacher=cls.teacher_b)
        cls.student_a = StudentProfile.objects.create(user=make_user('student_a', 'STUDENT'), class_arm=cls.arm_a)
        cls.student_b = StudentProfile.objects.create(user=make_user('student_b', 'STUDENT'), class_arm=cls.arm_b)

    def login(self, profile_or_user):
        self.client.force_login(getattr(profile_or_user, 'user', profile_or_user))


class AttendanceTests(PortalTestCase):
    def data_url(self, arm):
        return f'/e-portal/teacher-portal/attendance/date/{arm.id}/'

    def save(self, arm, records, on=None):
        payload = {'date': str(on or date.today()), 'records': records}
        return self.client.post(f'/e-portal/teacher-portal/attendance/date/save/{arm.id}/',
                                json.dumps(payload), content_type='application/json')

    def test_unmarked_day_defaults_to_present(self):
        # Used to crash: unpacking a 2-item default into 3 variables
        self.login(self.teacher_a)
        response = self.client.get(self.data_url(self.arm_a))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['status'], 'P')

    def test_teacher_cannot_read_or_save_another_arm(self):
        self.login(self.teacher_a)
        self.assertEqual(self.client.get(self.data_url(self.arm_b)).status_code, 403)
        response = self.save(self.arm_b, [{'student_id': self.student_b.id, 'status': 'A'}])
        self.assertEqual(response.status_code, 403)
        self.assertFalse(DailyAttendance.objects.exists())

    def test_saving_twice_updates_instead_of_duplicating(self):
        self.login(self.teacher_a)
        self.save(self.arm_a, [{'student_id': self.student_a.id, 'status': 'A'}])
        self.save(self.arm_a, [{'student_id': self.student_a.id, 'status': 'L'}])
        self.assertEqual(DailyAttendance.objects.count(), 1)
        self.assertEqual(DailyAttendance.objects.get().status, 'L')
        self.assertEqual(self.client.get(self.data_url(self.arm_a)).json()[0]['status'], 'L')

    def test_rejects_students_from_other_arms_and_bad_statuses(self):
        self.login(self.teacher_a)
        self.assertEqual(self.save(self.arm_a, [{'student_id': self.student_b.id, 'status': 'A'}]).status_code, 400)
        self.assertEqual(self.save(self.arm_a, [{'student_id': self.student_a.id, 'status': 'X'}]).status_code, 400)
        self.assertFalse(DailyAttendance.objects.exists())

    def test_rejects_future_dates(self):
        self.login(self.teacher_a)
        response = self.save(self.arm_a, [{'student_id': self.student_a.id, 'status': 'A'}],
                             on=date.today() + timedelta(days=1))
        self.assertEqual(response.status_code, 400)

    def test_overview_page_shows_saved_status(self):
        DailyAttendance.objects.create(student=self.student_a, class_arm=self.arm_a, date=date.today(),
                                       term=self.term, status='A')
        self.login(self.teacher_a)
        response = self.client.get('/e-portal/teacher-portal/attendance/')
        self.assertEqual(response.context['students_data_json'][0]['status'], 'A')


class PermissionTests(PortalTestCase):
    def test_teacher_sees_only_their_students(self):
        self.login(self.teacher_a)
        self.assertEqual(self.client.get(f'/e-portal/admin-portal/students/details/{self.student_a.id}').status_code, 200)
        self.assertEqual(self.client.get(f'/e-portal/admin-portal/students/details/{self.student_b.id}').status_code, 403)

    def test_subject_teacher_can_see_students_in_that_arm(self):
        SubjectAssignment.objects.create(class_arm=self.arm_b, session=self.session, teacher=self.teacher_a,
                                         subject=Subject.objects.create(name='Maths', code='MTH1'))
        self.login(self.teacher_a)
        self.assertEqual(self.client.get(f'/e-portal/admin-portal/students/details/{self.student_b.id}').status_code, 200)

    def test_teacher_pages_need_login(self):
        for url in ['/e-portal/teacher-portal/subject_assignments/', '/e-portal/teacher-portal/results/']:
            self.assertEqual(self.client.get(url).status_code, 302, url)

    def test_students_cannot_open_teacher_pages(self):
        self.login(self.student_a)
        self.assertEqual(self.client.get('/e-portal/teacher-portal/subject_assignments/').status_code, 403)


class ClassConsoleTests(PortalTestCase):
    def test_cannot_delete_arm_that_has_students(self):
        self.login(self.admin)
        response = self.client.delete(f'/e-portal/admin-portal/class-console/delete-arm/{self.arm_a.id}/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(ClassArm.objects.filter(id=self.arm_a.id).exists())

    def test_delete_needs_post_or_delete(self):
        self.login(self.admin)
        empty = ClassArm.objects.create(class_level=self.arm_a.class_level, name='C')
        self.assertEqual(self.client.get(f'/e-portal/admin-portal/class-console/delete-arm/{empty.id}/').status_code, 405)
        self.assertEqual(self.client.delete(f'/e-portal/admin-portal/class-console/delete-arm/{empty.id}/').status_code, 200)

    def test_cannot_add_duplicate_arm(self):
        self.login(self.admin)
        self.client.post(f'/e-portal/admin-portal/class-console/add-arm/{self.arm_a.class_level.id}/', {'name': 'a'})
        self.assertEqual(ClassArm.objects.filter(class_level=self.arm_a.class_level, name__iexact='A').count(), 1)


class SessionSettingsTests(PortalTestCase):
    def test_make_current_switches_session_and_term(self):
        new = AcademicSession.objects.create(name='2027/2028', start_year=2027, end_year=2028)
        new.create_default_terms()
        new.make_current()
        self.session.refresh_from_db()
        self.assertFalse(self.session.is_current)
        self.assertEqual(AcademicTerm.objects.get(is_current=True).session, new)

    def test_make_current_does_not_archive_sessions_being_planned(self):
        self.session.status = AcademicSession.SessionStatus.ACTIVE
        self.session.save()
        planning = AcademicSession.objects.create(name='2028/2029', start_year=2028, end_year=2029)
        new = AcademicSession.objects.create(name='2027/2028', start_year=2027, end_year=2028)
        new.make_current()
        self.session.refresh_from_db()
        planning.refresh_from_db()
        self.assertEqual(self.session.status, AcademicSession.SessionStatus.ARCHIVED)
        self.assertEqual(planning.status, AcademicSession.SessionStatus.PLANNING)
