"""
Tests for the Learner/Guardian/Teacher dashboard endpoints added in
views.py — the first frontend-facing surface built on top of the
nkowe_core domain model (see Nkowe_Core_Domain_Model_Phase2_Log.md).

Also exercises the LearnerIdentity auto-provisioning signal
(nkowe_core/signals.py) indirectly: every CustomUser created in these
tests is expected to already have a LearnerIdentity by the time
LearnerDashboardView is called, with no explicit backfill step in setUp.

Written but not yet run from this environment (no reachable Django/Python
execution environment — see the Week 1-2 regression test log's
explanation, which applies identically here). Please run
`python manage.py test nkowe_core` locally — this also serves as a real
end-to-end check that the nkowe_core migration (0001_initial +
0002_backfill_learner_identity) applies cleanly, which this session has
not been able to verify directly.
"""
from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from account.models import CustomUser, Parent, Student, Tutor, UserType
from classroom_app.classroom.models import Classroom, ClassroomStudent, ClassroomTutor
from classroom_app.definitions.insitution_types.models import InstitutionType
from classroom_app.institution.models import Institution
from nkowe_core.models import Enrollment, LearnerIdentity, LearnerRecordEvent, LearningJourney


def make_user(username, **extra):
    return CustomUser.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='not-a-real-password-123',
        **extra,
    )


def make_institution(email):
    institution_type = InstitutionType.objects.create(name=f'Type for {email}')
    return Institution.objects.create(
        name=f'Institution {email}', address='1 Main St', phone='555-0000',
        email=email, institution_type=institution_type,
    )


def make_student(user, **extra):
    defaults = {'state': '', 'country': '', 'address': '', 'grade_level': 'Elementary'}
    defaults.update(extra)
    return Student.objects.create(user=user, **defaults)


def make_tutor(user, **extra):
    defaults = {
        'state': '', 'country': '', 'address': '', 'qualification': '',
        'experience': '', 'description': '', 'availability': '', 'rate': 0,
        'background_check': '', 'references': '',
    }
    defaults.update(extra)
    return Tutor.objects.create(user=user, **defaults)


def make_classroom(institution, **extra):
    defaults = {'name': 'Test Classroom', 'institution': institution, 'capacity': 30}
    defaults.update(extra)
    return Classroom.objects.create(**defaults)


class LearnerDashboardViewTests(APITestCase):
    def setUp(self):
        self.user = make_user('learner_view')
        self.url = reverse('api:my-learning-record')

    def test_anonymous_request_is_rejected(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_signal_gave_the_user_a_learner_identity_already(self):
        """
        Guards against a regression in the create_learner_identity signal:
        if it stops firing (or the LearnerIdentity is deleted some other
        way), this endpoint should 404 rather than error, which the next
        test covers separately.
        """
        self.assertTrue(LearnerIdentity.objects.filter(user=self.user).exists())

    def test_authenticated_user_sees_their_own_identity_and_journeys(self):
        identity = LearnerIdentity.objects.get(user=self.user)
        institution = make_institution('learner-view@example.com')
        journey = LearningJourney.objects.create(
            learner=identity, institution=institution, title='Test Journey', started_at=date.today(),
        )
        Enrollment.objects.create(journey=journey, institution=institution, start_date=date.today())

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['user_id'], self.user.pk)
        self.assertEqual(len(response.data['journeys']), 1)
        self.assertEqual(len(response.data['journeys'][0]['enrollments']), 1)

    def test_user_without_a_learner_identity_gets_a_clean_404(self):
        LearnerIdentity.objects.filter(user=self.user).delete()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GuardianDashboardViewTests(APITestCase):
    def setUp(self):
        self.guardian_user = make_user('guardian_view')
        self.non_guardian_user = make_user('non_guardian_view')
        self.child_user = make_user('child_view')
        self.other_child_user = make_user('other_child_view')

        self.parent = Parent.objects.create(
            user=self.guardian_user, name='Guardian', email='guardian-profile@example.com',
            phone='555-1234', address='1 Guardian Way', relationship='Mother',
        )
        make_student(self.child_user, parent=self.parent)
        # A student NOT linked to this guardian's Parent profile.
        make_student(self.other_child_user)

        self.url = reverse('api:guardian-children-records')

    def test_anonymous_request_is_rejected(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_user_without_a_parent_profile_is_forbidden(self):
        self.client.force_authenticate(user=self.non_guardian_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_guardian_sees_only_their_own_linked_child(self):
        self.client.force_authenticate(user=self.guardian_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_usernames = {row['username'] for row in response.data}
        self.assertEqual(returned_usernames, {self.child_user.username})


class TeacherClassLearnerRecordsViewTests(APITestCase):
    def setUp(self):
        self.institution = make_institution('teacher-view@example.com')
        self.classroom = make_classroom(self.institution)
        self.other_classroom = make_classroom(self.institution, name='Other Classroom')

        self.tutor_user = make_user('teacher_view')
        self.tutor = make_tutor(self.tutor_user)
        ClassroomTutor.objects.create(classroom=self.classroom, tutor=self.tutor, role='TEACHER')

        self.outsider_user = make_user('outsider_teacher_view')

        self.student_user = make_user('roster_student_view')
        self.student = make_student(self.student_user)
        ClassroomStudent.objects.create(classroom=self.classroom, student=self.student)

        self.get_url = reverse('api:classroom-learner-records', kwargs={'classroom_id': self.classroom.pk})

    def test_non_tutor_cannot_view_the_roster(self):
        self.client.force_authenticate(user=self.outsider_user)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assigned_tutor_sees_the_roster(self):
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_usernames = {row['username'] for row in response.data}
        self.assertEqual(returned_usernames, {self.student_user.username})
        # The frontend roster view submits observations using this field
        # (not username) — regression coverage for that dependency.
        self.assertEqual(response.data[0]['user_id'], self.student_user.pk)

    def test_non_tutor_cannot_post_an_observation(self):
        self.client.force_authenticate(user=self.outsider_user)
        response = self.client.post(self.get_url, {
            'student_user_id': self.student_user.pk, 'note': 'Doing well.',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tutor_can_post_an_observation_for_a_roster_student(self):
        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.post(self.get_url, {
            'student_user_id': self.student_user.pk, 'note': 'Participates actively in class.',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        identity = LearnerIdentity.objects.get(user=self.student_user)
        event = LearnerRecordEvent.objects.get(learner=identity)
        self.assertEqual(event.provenance_category, LearnerRecordEvent.CATEGORY_OBSERVATION)
        self.assertEqual(event.responsible_actor, self.tutor_user)
        self.assertEqual(event.payload['note'], 'Participates actively in class.')

    def test_tutor_cannot_post_an_observation_for_a_non_roster_student(self):
        outsider_student_user = make_user('non_roster_student_view')
        make_student(outsider_student_user)

        self.client.force_authenticate(user=self.tutor_user)
        response = self.client.post(self.get_url, {
            'student_user_id': outsider_student_user.pk, 'note': 'Should be rejected.',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
