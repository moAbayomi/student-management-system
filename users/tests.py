import uuid
from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from profiles.models import StudentProfile, TeacherProfile
from profiles.services import StudentRegistrationService
from users.models import User


def make_teacher(expires_in=timedelta(days=7)):
    user = User(username='teach.abc123', role='TEACHER', email='t@school.test', first_name='Ada', is_active=False)
    user.set_unusable_password()
    user.save()
    return TeacherProfile.objects.create(
        user=user, status='PENDING_REVIEW',
        onboarding_token=uuid.uuid4(), onboarding_token_expires_at=timezone.now() + expires_in,
    )


class OnboardingTests(TestCase):
    def url(self, profile):
        return f'/users/onboard/{profile.onboarding_token}/'

    def test_page_shows_the_username(self):
        teacher = make_teacher()
        response = self.client.get(self.url(teacher))
        self.assertContains(response, 'teach.abc123')

    def test_setting_password_activates_account_and_burns_token(self):
        teacher = make_teacher()
        response = self.client.post(self.url(teacher), {
            'new_password1': 'a-Strong-pass-42', 'new_password2': 'a-Strong-pass-42'})
        self.assertTemplateUsed(response, 'users/onboarding/done.html')
        teacher.refresh_from_db()
        self.assertEqual(teacher.status, 'ACTIVE')
        self.assertIsNone(teacher.onboarding_token)
        self.assertTrue(teacher.user.is_active)
        self.assertTrue(self.client.login(username='teach.abc123', password='a-Strong-pass-42'))

    def test_mismatched_or_weak_passwords_are_rejected(self):
        teacher = make_teacher()
        self.client.post(self.url(teacher), {'new_password1': 'a-Strong-pass-42', 'new_password2': 'different-42'})
        self.client.post(self.url(teacher), {'new_password1': '123', 'new_password2': '123'})
        teacher.refresh_from_db()
        self.assertEqual(teacher.status, 'PENDING_REVIEW')
        self.assertFalse(teacher.user.has_usable_password())

    def test_unknown_token_is_404(self):
        self.assertEqual(self.client.get(f'/users/onboard/{uuid.uuid4()}/').status_code, 404)

    def test_expired_link_can_be_resent(self):
        teacher = make_teacher(expires_in=timedelta(days=-1))
        old_token = teacher.onboarding_token
        self.assertTemplateUsed(self.client.get(self.url(teacher)), 'users/onboarding/link_expired.html')

        self.client.post(f'/users/onboard/{old_token}/resend/')
        teacher.refresh_from_db()
        self.assertNotEqual(teacher.onboarding_token, old_token)
        self.assertGreater(teacher.onboarding_token_expires_at, timezone.now())
        self.assertEqual(mail.outbox[0].to, ['t@school.test'])

    def test_cannot_resend_a_link_that_is_still_valid(self):
        teacher = make_teacher()
        response = self.client.post(f'/users/onboard/{teacher.onboarding_token}/resend/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(mail.outbox), 0)


class StudentCreationTests(TestCase):
    def test_new_students_have_no_password_until_onboarded(self):
        # They used to get a hardcoded password that was visible in this public repo
        student = StudentRegistrationService.create_draft_student(
            {'first_name': 'Tolu', 'last_name': 'Ade', 'gender': 'F', 'dob': '2012-01-01'})
        self.assertIsInstance(student, StudentProfile)
        self.assertFalse(student.user.has_usable_password())
        self.assertFalse(student.user.is_active)
