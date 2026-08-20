"""
Regression tests for the Week 1-2 security stabilization pass on exam_app.

These exercise the fixes made to exam_app/serializers.py and
exam_app/views.py:
  - QuestionSerializer (used for every read of a question through
    ExamViewSet/QuestionViewSet) now nests PublicChoiceSerializer, which
    omits `is_correct`. It previously nested the full ChoiceSerializer, so
    any client fetching an exam or its questions received the correct
    answer to every multiple-choice question in the same response used to
    render the exam;
  - ExamViewSet/QuestionViewSet/ExamAttemptViewSet all require
    authentication (the project's global DEFAULT_PERMISSION_CLASSES is now
    IsAuthenticated — see nkowebe/settings.py — and each ViewSet also
    declares it explicitly);
  - ExamAttemptViewSet.get_queryset scopes attempts to the requesting
    student;
  - ScrapeQuestionsViewSet and SchoolNgrAccountsScrapeAPIView both issue
    server-side outbound HTTP requests to a caller-influenceable URL (an
    SSRF vector) and were previously fully unauthenticated
    (AllowAny/authentication_classes = []). Both are now restricted to
    Django staff/superusers (IsAdminUser).

Written but not yet run from this environment (no reachable Django/Python
execution environment — see the project's migration/CI notes). Please run
`python manage.py test exam_app` locally and report back any failures.
"""
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from account.models import CustomUser
from classroom_app.definitions.subjects.models import Subject
from exam_app.models import Choice, Exam, ExamAttempt, Question


def make_user(username, *, is_staff=False, **extra):
    return CustomUser.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='not-a-real-password-123',
        is_staff=is_staff,
        **extra,
    )


def make_exam(subject, **extra):
    defaults = {
        'title': 'Test Exam',
        'description': 'A test exam.',
        'duration': timedelta(hours=1),
        'total_marks': 10,
        'year': 2026,
        'passing_marks': 4,
        'start_time': timezone.now(),
        'end_time': timezone.now() + timedelta(hours=1),
        'is_published': True,
    }
    defaults.update(extra)
    return Exam.objects.create(subject=subject, **defaults)


class QuestionAnswerLeakTests(APITestCase):
    def setUp(self):
        self.user = make_user('examtaker')
        self.subject = Subject.objects.create(name='Mathematics', level='Beginner', category='STEM')
        self.exam = make_exam(self.subject)
        self.question = Question.objects.create(
            exam=self.exam, question_text='2 + 2 = ?', question_type='multiple_choice', marks=1, order=1
        )
        Choice.objects.create(question=self.question, choice_text='3', is_correct=False)
        Choice.objects.create(question=self.question, choice_text='4', is_correct=True)

    def test_questions_endpoint_rejects_anonymous_requests(self):
        response = self.client.get(reverse('api:question-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_question_choices_do_not_expose_is_correct(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('api:question-list'), {'exam_id': self.exam.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]['choices']), 2)
        for choice in results[0]['choices']:
            self.assertNotIn('is_correct', choice)
            self.assertIn('choice_text', choice)


class ExamAndAttemptPermissionTests(APITestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name='Physics', level='Beginner', category='STEM')
        self.exam = make_exam(self.subject)
        self.alice = make_user('alice_exam')
        self.bob = make_user('bob_exam')
        self.alice_attempt = ExamAttempt.objects.create(exam=self.exam, student=self.alice)
        self.bob_attempt = ExamAttempt.objects.create(exam=self.exam, student=self.bob)

    def test_exams_endpoint_rejects_anonymous_requests(self):
        response = self.client.get(reverse('api:exam-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_attempts_endpoint_rejects_anonymous_requests(self):
        response = self.client.get(reverse('api:attempt-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_attempts_are_scoped_to_the_requesting_student(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(reverse('api:attempt-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [row['custom_id'] for row in response.data],
            [str(self.alice_attempt.custom_id)],
        )


class ScrapeEndpointsStaffOnlyTests(APITestCase):
    """
    Both scraping endpoints fetch a caller-influenceable URL server-side
    (SSRF) and write results straight into the database — they must be
    unreachable by anyone but staff/superusers.
    """

    def setUp(self):
        self.user = make_user('regular_scrape')
        self.staff = make_user('staff_scrape', is_staff=True)

    def test_scrape_questions_rejects_anonymous_requests(self):
        response = self.client.post(reverse('api:scrape-questions-scrape_questions'), {})
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_scrape_questions_rejects_non_staff_users(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('api:scrape-questions-scrape_questions'), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_ngr_scrape_rejects_anonymous_requests(self):
        response = self.client.post(reverse('api:scrape-questions2'), {})
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_school_ngr_scrape_rejects_non_staff_users(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('api:scrape-questions2'), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
