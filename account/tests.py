"""
Regression tests for the Week 1-2 security stabilization pass (see
Nkowe_Week1-2_Security_Stabilization_Remediation_Log.md in the Electroll
Documentation project for the full write-up). Written but not yet run from
this environment -- the device bridge used to edit this codebase has no
Django execution environment available (Windows-only venv, no network in
the bridge's own shell) -- so please run `python manage.py test account`
locally and report back anything that fails; these are meant to lock in
the fixes, not to be taken on faith.
"""
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from account.models import Admin, CustomUser, Moderator, Teacher, UserType


def make_user_type(name):
    user_type, _ = UserType.objects.get_or_create(
        name=name, defaults={'description': name, 'is_active': True}
    )
    return user_type


def make_user(username, *, is_staff=False, user_type_name=None, **extra):
    user = CustomUser.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='not-a-real-password-123',
        is_staff=is_staff,
        **extra,
    )
    if user_type_name:
        user.user_type = make_user_type(user_type_name)
        user.save(update_fields=['user_type'])
    return user


class CustomUserViewSetPermissionTests(APITestCase):
    """
    Was fully open (no permission_classes at all) -- anyone on the internet
    could list, create, update, or delete any user account with no
    authentication. Now: IsAuthenticated, and non-staff users only see
    their own record.
    """

    def setUp(self):
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        self.staff = make_user('staffer', is_staff=True)
        self.url = reverse('api:custom-users-list')

    def test_anonymous_request_is_rejected(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_non_staff_user_sees_only_their_own_record(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {row['id'] for row in response.data}
        self.assertEqual(returned_ids, {self.alice.id})

    def test_staff_user_sees_every_record(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {row['id'] for row in response.data}
        self.assertEqual(returned_ids, {self.alice.id, self.bob.id, self.staff.id})


class AdminAndModeratorViewSetPermissionTests(APITestCase):
    """Both were fully open (no permission_classes). Now IsAdminUser (Django staff)."""

    def setUp(self):
        self.regular = make_user('regular_user')
        self.staff = make_user('staff_user', is_staff=True)

    def _assert_staff_only(self, url):
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(user=self.regular)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_endpoint_is_staff_only(self):
        Admin.objects.create(user=self.staff)
        self._assert_staff_only(reverse('api:admins-list'))

    def test_moderator_endpoint_is_staff_only(self):
        Moderator.objects.create(user=self.staff)
        self._assert_staff_only(reverse('api:moderators-list'))


class RegisterAndLoginRemainPublicTests(APITestCase):
    """
    settings.py now sets a project-wide default of IsAuthenticated. These
    two endpoints are the ones that must stay reachable by a logged-out
    client regardless -- they're how a client becomes authenticated in the
    first place. This only asserts they weren't accidentally locked behind
    auth; it doesn't assert a full successful registration/login (which
    depends on serializer fields this test file doesn't need to know).
    """

    def test_register_endpoint_does_not_require_authentication(self):
        response = self.client.post(reverse('api:register-list'), data={}, format='json')
        self.assertNotIn(
            response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        )

    def test_login_endpoint_does_not_require_authentication(self):
        response = self.client.post(reverse('api:login-list'), data={}, format='json')
        self.assertNotIn(
            response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        )


class TeacherViewSetRoleScopingTests(APITestCase):
    """
    TeacherViewSet.get_queryset() compared `user.user_type == 'teacher'` --
    a ForeignKey object compared to a string literal, always False -- so a
    real teacher's "only see my own record" self-scoping never applied.
    Fixed via user_has_type(). This test authenticates as an actual teacher
    and checks the list is scoped down to just their own record.
    """

    def setUp(self):
        self.teacher_a = make_user('teacher_a', user_type_name='Teacher')
        self.teacher_b = make_user('teacher_b', user_type_name='Teacher')
        Teacher.objects.create(
            user=self.teacher_a,
            subject_specialization='Mathematics',
            experience='5 years',
            qualifications='B.Ed',
            state='Lagos',
            country='Nigeria',
            address='n/a',
        )
        Teacher.objects.create(
            user=self.teacher_b,
            subject_specialization='Physics',
            experience='3 years',
            qualifications='B.Sc',
            state='Lagos',
            country='Nigeria',
            address='n/a',
        )

    def test_authenticated_teacher_sees_only_their_own_record(self):
        self.client.force_authenticate(user=self.teacher_a)
        response = self.client.get(reverse('api:teacher-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The exact serializer shape isn't the point of this test; what
        # matters is that exactly one record comes back (not both teachers),
        # proving the self-scoping filter actually applied.
        self.assertEqual(len(response.data), 1)
