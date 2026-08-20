"""
Regression tests for the Week 1-2 security stabilization pass on
classroom_app.

These exercise the fixes made to classroom_app/classroom/views.py and
classroom_app/institution/views.py:
  - ClassroomStudentViewSet/ClassroomTutorViewSet/ClassroomExaminationViewSet/
    ClassroomAttachmentViewSet previously required only IsAuthenticated and
    filtered solely by an optional `classroom_id` query param, with no check
    that the requesting user actually belonged to that classroom — any
    authenticated user could read (and, being ModelViewSets, write) another
    classroom's student roster, tutor roster, exams, or attachments simply
    by passing its ID, or see every classroom's data at once by omitting it.
    scoped_by_classroom_membership() now restricts each of these to
    classrooms the requester is actually enrolled in (as a student) or
    assigned to (as a tutor), with staff/superusers exempted;
  - InstitutionEnrollmentViewSet.enroll_student/enroll_staff previously had
    NO authorization check at all (the code said "Check permissions...
    skipped for brevity/MVP" and then didn't), so any authenticated user
    could enroll students or staff into ANY institution. Both actions now
    require user_can_manage_institution() — the caller must be the
    institution's registered owner or an Administrator staff member there.

Written but not yet run from this environment (no reachable Django/Python
execution environment — see the project's migration/CI notes). Please run
`python manage.py test classroom_app` locally and report back any failures.
"""
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from account.models import Administrator, CustomUser, InstitutionalOwner, Student, Tutor
from classroom_app.classroom.models import Classroom, ClassroomStudent, ClassroomTutor
from classroom_app.definitions.insitution_types.models import InstitutionType
from classroom_app.institution.models import Institution


def make_user(username, **extra):
    return CustomUser.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='not-a-real-password-123',
        **extra,
    )


def make_institution(email, **extra):
    institution_type = InstitutionType.objects.create(name=f'Type for {email}')
    defaults = {
        'name': f'Institution {email}',
        'address': '1 Main St',
        'phone': '555-0000',
        'email': email,
        'institution_type': institution_type,
    }
    defaults.update(extra)
    return Institution.objects.create(**defaults)


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


class ClassroomRosterScopingTests(APITestCase):
    def setUp(self):
        self.institution_a = make_institution('inst-a@example.com')
        self.institution_b = make_institution('inst-b@example.com')
        self.classroom_a = make_classroom(self.institution_a, name='Classroom A')
        self.classroom_b = make_classroom(self.institution_b, name='Classroom B')

        self.student_a_user = make_user('student_a')
        self.student_a = make_student(self.student_a_user)
        self.classroom_a_membership = ClassroomStudent.objects.create(
            classroom=self.classroom_a, student=self.student_a
        )

        self.student_b_user = make_user('student_b')
        self.student_b = make_student(self.student_b_user)
        self.classroom_b_membership = ClassroomStudent.objects.create(
            classroom=self.classroom_b, student=self.student_b
        )

        self.outsider = make_user('outsider_roster')

    def test_anonymous_request_is_rejected(self):
        response = self.client.get(reverse('api:classroom_students-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_member_sees_only_their_own_classrooms_roster(self):
        self.client.force_authenticate(user=self.student_a_user)
        response = self.client.get(reverse('api:classroom_students-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row['id'] for row in response.data], [self.classroom_a_membership.pk])

    def test_non_member_cannot_see_a_classroom_roster_by_passing_its_id(self):
        """
        The pre-fix behavior: any authenticated user could pass another
        classroom's ID via ?classroom_id= and read its roster. Membership
        scoping now excludes it regardless of the query param.
        """
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(
            reverse('api:classroom_students-list'), {'classroom_id': self.classroom_a.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_non_member_sees_nothing_across_all_classrooms(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(reverse('api:classroom_students-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_staff_user_sees_every_classrooms_roster(self):
        staff = make_user('staff_roster', is_staff=True)
        self.client.force_authenticate(user=staff)
        response = self.client.get(reverse('api:classroom_students-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {row['id'] for row in response.data}
        self.assertEqual(returned_ids, {self.classroom_a_membership.pk, self.classroom_b_membership.pk})


class ClassroomTutorRosterScopingTests(APITestCase):
    def setUp(self):
        self.institution = make_institution('inst-tutor@example.com')
        self.classroom_a = make_classroom(self.institution, name='Classroom A')
        self.classroom_b = make_classroom(self.institution, name='Classroom B')

        self.tutor_a_user = make_user('tutor_a')
        self.tutor_a = make_tutor(self.tutor_a_user)
        self.classroom_a_assignment = ClassroomTutor.objects.create(
            classroom=self.classroom_a, tutor=self.tutor_a, role='TEACHER'
        )

        self.tutor_b_user = make_user('tutor_b')
        self.tutor_b = make_tutor(self.tutor_b_user)
        ClassroomTutor.objects.create(classroom=self.classroom_b, tutor=self.tutor_b, role='TEACHER')

    def test_tutor_sees_only_their_own_classroom_assignments(self):
        self.client.force_authenticate(user=self.tutor_a_user)
        response = self.client.get(reverse('api:classroom_tutors-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row['id'] for row in response.data], [self.classroom_a_assignment.pk])


class InstitutionEnrollmentAuthorizationTests(APITestCase):
    def setUp(self):
        self.institution = make_institution('enroll-inst@example.com')

        self.owner_user = make_user('inst_owner')
        InstitutionalOwner.objects.create(
            user=self.owner_user, institution=self.institution,
            phone='555-1111', email='owner@example.com',
        )

        self.admin_user = make_user('inst_admin')
        admin_profile = Administrator.objects.create(user=self.admin_user)
        admin_profile.institutions.add(self.institution)

        self.unauthorized_user = make_user('rando_enroller')

        self.enroll_student_url = reverse(
            'api:institution-enrollment-enroll-student', kwargs={'pk': self.institution.pk}
        )
        self.enroll_staff_url = reverse(
            'api:institution-enrollment-enroll-staff', kwargs={'pk': self.institution.pk}
        )

    def test_unauthorized_user_cannot_enroll_a_student(self):
        self.client.force_authenticate(user=self.unauthorized_user)
        response = self.client.post(self.enroll_student_url, {
            'first_name': 'New', 'last_name': 'Student',
            'email': 'newstudent@example.com', 'grade_level': 'Elementary',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(CustomUser.objects.filter(email='newstudent@example.com').exists())

    def test_unauthorized_user_cannot_enroll_staff(self):
        self.client.force_authenticate(user=self.unauthorized_user)
        response = self.client.post(self.enroll_staff_url, {
            'first_name': 'New', 'last_name': 'Tutor',
            'email': 'newtutor@example.com', 'role': 'tutor',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(CustomUser.objects.filter(email='newtutor@example.com').exists())

    def test_institution_owner_can_enroll_a_student(self):
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.post(self.enroll_student_url, {
            'first_name': 'New', 'last_name': 'Student',
            'email': 'ownerenrolled@example.com', 'grade_level': 'Elementary',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email='ownerenrolled@example.com').exists())

    def test_institution_administrator_can_enroll_a_student(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.enroll_student_url, {
            'first_name': 'New', 'last_name': 'Student',
            'email': 'adminenrolled@example.com', 'grade_level': 'Elementary',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email='adminenrolled@example.com').exists())
