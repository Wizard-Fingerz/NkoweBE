import datetime
import csv
import requests
import os
from bs4 import BeautifulSoup
from rest_framework import status, viewsets, permissions, pagination
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework.permissions import AllowAny

from classroom_app.definitions.examination_types.models import ExaminationType
from classroom_app.definitions.subjects.models import Subject
from .models import Choice, Exam, Question, ExamAttempt, Answer
from .serializers import (
    ExamSerializer, ExamCreateSerializer,
    QuestionSerializer, QuestionCreateSerializer,
    ExamAttemptSerializer, ExamSubmissionSerializer, ScrapeQuestionsSerializer,
    StaffExamCreateSerializer
)
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Avg

# Custom Pagination remains unchanged
class CustomPagination(pagination.PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 12

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'num_pages': self.page.paginator.num_pages,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'results': data
        })


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'user_type'):
            return Exam.objects.none()
        if user.user_type == 'teacher':
            return Exam.objects.all().order_by('-year')
        elif user.user_type == 'student':
            return Exam.objects.filter(examination_type=user.examination_type).order_by('-year')
        return Exam.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            if self.request.user.user_type == 'teacher':
                return StaffExamCreateSerializer if self.action == 'create' else ExamCreateSerializer
            return ExamCreateSerializer
        return ExamSerializer

    def perform_create(self, serializer):
        user = self.request.user
        subject_id = self.request.data.get('subject')
        if user.user_type != 'teacher':
            raise PermissionDenied("Only teachers can create exams.")
        if not subject_id:
            raise PermissionDenied("Subject ID is required.")
        try:
            subject = Subject.objects.get(pk=subject_id)
        except Subject.DoesNotExist:
            raise PermissionDenied("Subject not found.")
        serializer.save(subject=subject)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        if user.user_type != 'teacher' or getattr(instance.subject, 'instructor', None) != user:
            raise PermissionDenied("Only the subject instructor can update the exam.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.user_type != 'teacher' or getattr(instance.subject, 'instructor', None) != user:
            raise PermissionDenied("Only the subject instructor can delete the exam.")
        instance.delete()

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def analytics(self, request, pk=None):
        exam = self.get_object()
        user = request.user
        if user.user_type != 'teacher' or getattr(exam.subject, 'instructor', None) != user:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        attempts = ExamAttempt.objects.filter(exam=exam)
        total_attempts = attempts.count()
        completed_attempts = attempts.filter(submitted_at__isnull=False).count()
        average_score = attempts.filter(submitted_at__isnull=False).aggregate(avg_score=Avg('score'))['avg_score'] or 0
        passing_rate = (attempts.filter(score__gte=exam.passing_marks).count() / completed_attempts * 100) if completed_attempts > 0 else 0

        return Response({
            'total_attempts': total_attempts,
            'completed_attempts': completed_attempts,
            'average_score': average_score,
            'passing_rate': passing_rate
        })


class QuestionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        # Accepts 'exam_pk' as kwarg from router
        exam_id = self.kwargs.get('exam_pk') or self.request.query_params.get('exam_id')
        if exam_id:
            return Question.objects.filter(exam_id=exam_id)
        return Question.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateSerializer
        return QuestionSerializer

    def perform_create(self, serializer):
        exam_id = self.kwargs.get('exam_pk') or self.request.data.get('exam')
        if not exam_id:
            raise PermissionDenied("Exam ID required for creating questions.")
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            raise PermissionDenied("Exam not found.")
        serializer.save(exam=exam)


class ExamAttemptViewSet(viewsets.ModelViewSet):
    queryset = ExamAttempt.objects.all()
    serializer_class = ExamAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExamAttempt.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        exam_id = self.request.data.get('exam') or self.kwargs.get('exam_pk') or self.kwargs.get('pk')
        if not exam_id:
            raise PermissionDenied("Exam ID is required.")
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            raise PermissionDenied("Exam not found.")
        serializer.save(student=self.request.user, exam=exam)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        attempt = self.get_object()
        if attempt.student != request.user:
            return Response({"detail": "You can only submit your own exam attempts."}, status=status.HTTP_403_FORBIDDEN)
        if getattr(attempt, "is_completed", False):
            return Response({"detail": "This exam attempt has already been completed."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ExamSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(attempt=attempt)
            return Response({'status': 'submission complete'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScrapeQuestionsViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=ScrapeQuestionsSerializer)
    @action(detail=False, methods=['post'], url_path="scrape", url_name="scrape_questions")
    def scrape(self, request):
        serializer = ScrapeQuestionsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated fields
        subject_name = serializer.validated_data['subject']
        year = serializer.validated_data['year']
        max_pages = serializer.validated_data['pages']
        slug = serializer.validated_data['slug']
        exam_type = serializer.validated_data.get('exam_type')  # Now exam_type is in request

        if not all([subject_name, year, slug, exam_type]):
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        # Use exam_type for URL construction if needed (fall back to legacy behaviour for URL if required)
        BASE_URL = 'https://nigerianscholars.com'
        BASE_PATH = f'/past-questions/{slug}/{exam_type.lower()}/year/{year}/'
        HEADERS = {
            "User-Agent": "Mozilla/5.0"
        }

        questions = []

        for page in range(1, max_pages + 1):
            if page == 1:
                url = BASE_URL + BASE_PATH
            else:
                url = f"{BASE_URL}{BASE_PATH}page/{page}/"

            print(f"Scraping: {url}")
            response = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')

            page_questions = []
            for q_div in soup.select('.question_block'):
                question_el = q_div.select_one('.question_text')
                question_text = question_el.get_text(strip=True) if question_el else None

                options = [opt.get_text(strip=True) for opt in q_div.select('.q_option')]

                answer_el = q_div.select_one('.ans_label')
                answer = answer_el.get_text(strip=True) if answer_el else None

                page_questions.append({
                    'question': question_text,
                    'options': options,
                    'answer': answer
                })

            if not page_questions:
                break
            questions.extend(page_questions)

        subject, _ = Subject.objects.get_or_create(name=subject_name)
        
        try:
            exam_type_obj = ExaminationType.objects.get(name__iexact=exam_type)
        except ExaminationType.DoesNotExist:
            return Response({"error": f"ExaminationType '{exam_type}' not found."}, status=status.HTTP_400_BAD_REQUEST)

        exam, _ = Exam.objects.get_or_create(
            subject=subject,
            title=f"{exam_type.upper()} {year} {subject_name}",
            examination_type=exam_type_obj,
            defaults={
                "description": f"{exam_type.upper()} {year} {subject_name} Questions",
                "duration": timezone.timedelta(seconds=3600),
                "total_marks": 100,
                "year": year,
                "passing_marks": 40,
                "start_time": timezone.now(),
                "end_time": timezone.now() + timezone.timedelta(hours=1),
                "is_published": True,
            }
        )

        for idx, q in enumerate(questions, start=1):
            question_obj = Question.objects.create(
                exam=exam,
                question_text=q['question'],
                question_type='multiple_choice',
                marks=1,
                order=idx
            )
            for opt in q['options']:
                is_correct = (opt == q['answer'])
                Choice.objects.create(
                    question=question_obj,
                    choice_text=opt,
                    is_correct=is_correct
                )

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f'scraped_questions_{timestamp}.csv'
        csv_path = os.path.join("media", csv_filename)

        os.makedirs("media", exist_ok=True)
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['question_text', 'option_1', 'option_2',
                             'option_3', 'option_4', 'correct_option'])
            for q in questions:
                row = [
                    q['question'],
                    q['options'][0] if len(q['options']) > 0 else '',
                    q['options'][1] if len(q['options']) > 1 else '',
                    q['options'][2] if len(q['options']) > 2 else '',
                    q['options'][3] if len(q['options']) > 3 else '',
                    q['answer'] or ''
                ]
                writer.writerow(row)

        return Response({
            "message": "Scraping complete",
            "questions_scraped": len(questions),
            "csv_file": csv_filename
        }, status=200)

