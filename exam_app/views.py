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
    StaffExamCreateSerializer, PracticeExamSerializer
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
    from rest_framework.authentication import TokenAuthentication
    authentication_classes = [TokenAuthentication]

    # def get_queryset(self):
    #     user = self.request.user
    #     if not user.is_authenticated or not hasattr(user, 'user_type'):
    #         return Exam.objects.all()
    #     if user.user_type == 'teacher':
    #         return Exam.objects.all().order_by('-year')
    #     elif user.user_type == 'student':
    #         # return Exam.objects.filter(examination_type=user.examination_type).order_by('-year')
    #         return Exam.objects.all().order_by('-year')
    #     return Exam.objects.none()

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
            raise PermissionDenied(
                "Only the subject instructor can update the exam.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.user_type != 'teacher' or getattr(instance.subject, 'instructor', None) != user:
            raise PermissionDenied(
                "Only the subject instructor can delete the exam.")
        instance.delete()

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def analytics(self, request, pk=None):
        exam = self.get_object()
        user = request.user
        if user.user_type != 'teacher' or getattr(exam.subject, 'instructor', None) != user:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        attempts = ExamAttempt.objects.filter(exam=exam)
        total_attempts = attempts.count()
        completed_attempts = attempts.filter(
            submitted_at__isnull=False).count()
        average_score = attempts.filter(submitted_at__isnull=False).aggregate(
            avg_score=Avg('score'))['avg_score'] or 0
        passing_rate = (attempts.filter(score__gte=exam.passing_marks).count(
        ) / completed_attempts * 100) if completed_attempts > 0 else 0

        return Response({
            'total_attempts': total_attempts,
            'completed_attempts': completed_attempts,
            'average_score': average_score,
            'passing_rate': passing_rate
        })


class QuestionViewSet(viewsets.ModelViewSet):
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        # Accepts 'exam_pk' as kwarg from router
        exam_id = self.kwargs.get(
            'exam_pk') or self.request.query_params.get('exam_id')
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
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExamAttempt.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        exam_id = self.request.data.get('exam') or self.kwargs.get(
            'exam_pk') or self.kwargs.get('pk')
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


class PracticeExamViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for listing/retrieving practice exams, including their questions and expected answers.
    Intended for practice or study-mode quizzes, not official submissions.
    """
    serializer_class = PracticeExamSerializer
    permission_classes = [permissions.AllowAny]  # Allow everyone to view practice exams

    def get_queryset(self):
        # Only list exams that are published (for practice purposes)
        return Exam.objects.filter(is_published=True)

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """
        Returns all practice questions for this exam, including expected answers.
        """
        exam = self.get_object()
        serializer = self.get_serializer(exam)
        return Response(serializer.data)


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
        exam_type = serializer.validated_data.get(
            'exam_type')  # Now exam_type is in request

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
                question_text = question_el.get_text(
                    strip=True) if question_el else None

                options = [opt.get_text(strip=True)
                           for opt in q_div.select('.q_option')]

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

import requests
from bs4 import BeautifulSoup
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.utils import timezone

from .models import Exam, Question, Choice

import re
from rest_framework import serializers

class SchoolNgrScrapeInputSerializer(serializers.Serializer):
    base_url = serializers.CharField(
        help_text="Classroom listing page URL with '{page_num}' placeholder, e.g. https://www.schoolngr.com/classroom/waec/accounts-principles-of-accounts?page={page_num}")
    start_page = serializers.IntegerField(default=1, min_value=1, help_text="First page number to scrape")
    end_page = serializers.IntegerField(default=1, min_value=1, help_text="Last page number to scrape (inclusive)")
    title = serializers.CharField(required=False, allow_blank=True, help_text="Exam or scrape job title")
    subject_id = serializers.IntegerField(required=False, allow_null=True, help_text="Optional subject ID")
    examination_type = serializers.CharField(required=False, allow_blank=True, help_text="Exam type, e.g. WAEC/NECO")
    year = serializers.CharField(required=False, allow_blank=True, help_text="Exam year or 'Mixed'", default="Mixed")

class SchoolNgrScrapeOutputQuestionSerializer(serializers.Serializer):
    question_text = serializers.CharField()
    year = serializers.CharField(allow_blank=True, required=False)
    options = serializers.ListField(
        child=serializers.CharField(), allow_empty=True
    )
    answer = serializers.CharField(allow_blank=True, required=False, allow_null=True)

class SchoolNgrScrapeOutputSerializer(serializers.Serializer):
    message = serializers.CharField()
    exam_id = serializers.IntegerField()
    exam_title = serializers.CharField()
    questions_scraped = serializers.IntegerField()
    questions = SchoolNgrScrapeOutputQuestionSerializer(many=True)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
class SchoolNgrAccountsScrapeAPIView(APIView):
    """
    API endpoint to scrape questions from any page on schoolngr.com (or similar)
    and save them as an Exam with Questions/Choices.

    POST data:
        {
            "base_url": "https://www.schoolngr.com/classroom/waec/accounts-principles-of-accounts?page={page_num}",
            "start_page": 1,
            "end_page": 2,
            "title": "WAEC Accounts - Principles of Accounts",
            "subject_id": null,
            "examination_type": "WAEC",
            "year": "Mixed"
        }
    - base_url MUST include "{page_num}" as its page number placeholder.
    """
    permission_classes = [AllowAny]

    def parse_exam_type_and_subject_from_url(self, url):
        """
        Tries to extract exam type (examination_type) and subject key from the schoolngr classroom URL, e.g.:
            https://www.schoolngr.com/classroom/waec/accounts-principles-of-accounts?page=1
            => exam_type: WAEC, subject: ACCOUNTS PRINCIPLES OF ACCOUNTS
        Returns (exam_type, subject_name) or (None, None) if can't be parsed.
        """
        print("[Stage] Parsing exam type and subject from URL...")  # Progress print
        match = re.search(r'classroom/([^/]+)/([^/?&]+)', url)
        if match:
            exam_type = match.group(1).upper()
            raw_subject = match.group(2)
            subject_name = raw_subject.replace('-', ' ').replace('_', ' ').title()
            print(f"[Stage Done] Extracted exam_type: {exam_type}, subject: {subject_name}")  # Progress print
            return exam_type, subject_name
        print("[Stage Fail] Could not extract exam_type and subject from URL.")  # Progress print
        return None, None

    @swagger_auto_schema(
        request_body=SchoolNgrScrapeInputSerializer,
        responses={201: SchoolNgrScrapeOutputSerializer}
    )
    def post(self, request):
        print("[Stage] Validating input data...")  # Progress print
        serializer = SchoolNgrScrapeInputSerializer(data=request.data)
        if not serializer.is_valid():
            print("[Stage Fail] Invalid input data.")  # Progress print
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        base_url = data.get("base_url")
        if not base_url or "{page_num}" not in base_url:
            print("[Stage Fail] base_url missing or invalid.")  # Progress print
            return Response(
                {"error": "Please provide base_url with '{page_num}' in its value."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        start_page = int(data.get("start_page", 1))
        end_page = int(data.get("end_page", 1))
        title = data.get("title")
        subject_id = data.get("subject_id")
        examination_type = data.get("examination_type")
        year = data.get("year", "Mixed")

        print("[Stage] Inferring exam type/title from URL if needed...")  # Progress print
        # Try to infer examination_type and subject_name if missing
        parsed_exam_type, parsed_subject_name = self.parse_exam_type_and_subject_from_url(base_url)
        if not examination_type and parsed_exam_type:
            examination_type = parsed_exam_type
        if not title and parsed_subject_name and examination_type:
            title = f"{examination_type} {parsed_subject_name}"
        if not title:
            title = "SchoolNGR Questions"

        print("[Stage] Starting scraping of questions...")  # Progress print
        # Scrape questions
        scraped_questions = self.scrape_schoolngr_accounts_questions(base_url, start_page, end_page)

        print(f"[Stage Done] Scraped {len(scraped_questions)} questions.")  # Progress print

        # Try to extract a common year from all questions, fallback assignment
        years_found = [q.get('year', '').strip() for q in scraped_questions if q.get('year', '').strip()]
        year_for_exam = None
        print("[Stage] Analyzing years from scraped questions...")  # Progress print
        if years_found:
            unique_years = set(years_found)
            if len(unique_years) == 1:
                year_for_exam = years_found[0]
                print(f"[Stage Done] Unique year for exam: {year_for_exam}")  # Progress print
            else:
                year_for_exam = "Mixed"
                print(f"[Stage Done] Mixed years found: {unique_years}")  # Progress print
        else:
            year_for_exam = year or "Mixed"
            print("[Stage Done] No years found, using fallback value.")  # Progress print

        exam_description_parts = [f"Past questions scraped from {base_url} (pages {start_page}-{end_page})"]
        if parsed_subject_name and not subject_id:
            exam_description_parts.append(f"Subject: {parsed_subject_name}")

        print("[Stage] Preparing Exam record (get_or_create)...")  # Progress print
        exam_defaults = {
            "description": "; ".join(exam_description_parts),
            "duration": 120,
            "total_marks": len(scraped_questions),
            "passing_marks": int(len(scraped_questions) * 0.4),
            "examination_type": examination_type if examination_type else "",
            "year": int(year_for_exam) if str(year_for_exam).isdigit() else 0,
            "start_time": timezone.now(),
            "end_time": timezone.now() + timezone.timedelta(hours=2),
            "is_published": False,
        }
        if subject_id:
            exam_defaults["subject_id"] = subject_id

        exam, _ = Exam.objects.get_or_create(
            title=title,
            defaults=exam_defaults
        )
        print(f"[Stage Done] Exam set: '{exam.title}' (ID: {exam.id})")  # Progress print

        created_questions = []
        print("[Stage] Creating Question and Choice records...")  # Progress print
        for idx, q in enumerate(scraped_questions, start=1):
            # Extract year per question if present and not empty, fallback to exam year or None
            question_year = q.get('year', '').strip()
            if not question_year:
                question_year = str(year_for_exam) if year_for_exam else ""
            # The Question model doesn't take year, but you could log, or add field if needed
            question_obj = Question.objects.create(
                exam=exam,
                question_text=q['question'],
                question_type='multiple_choice' if q.get('options') else 'short_answer',
                marks=1,
                order=idx
            )
            for opt in (q.get('options') or []):
                is_correct = (opt == q.get('answer'))
                Choice.objects.create(
                    question=question_obj,
                    choice_text=opt,
                    is_correct=is_correct
                )
            created_questions.append({
                "question_text": question_obj.question_text,
                "year": question_year,
                "options": q.get('options'),
                "answer": q.get('answer'),
            })
            print(f"[Stage Done] Created question {idx}: {question_obj.question_text[:40]}...")  # Progress print

        print("[Stage] Finalizing and returning response...")  # Progress print
        output_data = {
            "message": "Scraping complete",
            "exam_id": exam.id,
            "exam_title": exam.title,
            "questions_scraped": len(scraped_questions),
            "questions": created_questions,
        }
        out_serializer = SchoolNgrScrapeOutputSerializer(output_data)
        print("[Stage Done] Response ready!")  # Progress print
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def scrape_schoolngr_accounts_questions(self, base_url, start_page=1, end_page=1):
        """
        Scrape questions from the provided base_url, paginated with '{page_num}'.

        Returns:
            questions: [
                {
                    'question': str,
                    'options': [str, ...],  # possibly empty
                    'answer': str or None,  # right option or None
                    'year': str,
                }
            ]
        """
        questions = []
        session = requests.Session()
        print("[Stage] Starting question scraping loop...")  # Progress print

        for page_num in range(start_page, end_page + 1):
            url = base_url.format(page_num=page_num)
            print(f"[Stage] Scraping page {page_num}: {url}")  # Progress print
            try:
                resp = session.get(url)
            except Exception as e:
                print(f"[Stage Fail] Exception occurred loading page {page_num}: {e}")
                continue
            if resp.status_code != 200:
                print(f"[Stage Fail] Failed to load page {page_num} (status: {resp.status_code})")  # Progress print
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            questions_blocks = soup.select(".question-block")
            print(f"[Stage] Found {len(questions_blocks)} questions on page {page_num}.")  # Progress print
            for block in questions_blocks:
                # Extract question text
                question_text_div = block.find("div", class_="question-text")
                qtext = question_text_div.get_text(separator=" ", strip=True) if question_text_div else ""
                # Try to extract year from either question-year div or from question text itself
                year_div = block.find("div", class_="question-year")
                year = year_div.get_text(strip=True) if year_div else ""
                if not year:
                    # Try to extract year pattern like '2019' or '2022' from question text
                    match = re.search(r"(19|20)\d{2}", qtext)
                    if match:
                        year = match.group(0)
                # Option parsing
                options_ul = block.select_one('.options.quiz-options ul')
                options = []
                answer = None
                if options_ul:
                    for li in options_ul.find_all('li'):
                        label = li.select_one('.option-label')
                        text = li.get_text(separator=" ", strip=True)
                        # Remove label at start (e.g., "A"), if present
                        if label:
                            label_text = label.get_text(strip=True)
                            if text.startswith(label_text):
                                option_val = text[len(label_text):].strip()
                            else:
                                option_val = text
                        else:
                            option_val = text
                        options.append(option_val)
                        if li.has_attr('data-correct') and li['data-correct'] == "true":
                            answer = option_val
                questions.append({
                    "question": qtext,
                    "options": options,
                    "answer": answer,
                    "year": year,
                })
            print(f"[Stage Done] Finished processing page {page_num}.")  # Progress print
        print(f"[Stage Done] Total scraped questions: {len(questions)}")  # Progress print
        return questions

