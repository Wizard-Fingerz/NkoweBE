from django.db import models
from django.conf import settings
import uuid

from classroom_app.definitions.examination_types.models import ExaminationType
from classroom_app.definitions.subjects.models import Subject

def generate_unique_uuid(model, field_name='custom_id'):
    """
    Attempts to generate a truly unique UUID for a given model and field.
    This avoids collisions even if old data has duplicates (particularly during migrations!).
    """
    while True:
        new_uuid = uuid.uuid4()
        if not model.objects.filter(**{field_name: new_uuid}).exists():
            return new_uuid

class Exam(models.Model):
    custom_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams_subjects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.DurationField()
    total_marks = models.PositiveIntegerField()
    examination_type = models.ForeignKey(ExaminationType, null=True, blank=True, on_delete=models.SET_NULL)
    year = models.PositiveIntegerField()
    passing_marks = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Guarantee unique custom_id even if old data exists
        if self.custom_id is None or self.__class__.objects.filter(custom_id=self.custom_id).exclude(pk=self.pk).exists():
            self.custom_id = generate_unique_uuid(self.__class__)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

class Question(models.Model):
    custom_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    )
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    marks = models.PositiveIntegerField()
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def save(self, *args, **kwargs):
        if self.custom_id is None or self.__class__.objects.filter(custom_id=self.custom_id).exclude(pk=self.pk).exists():
            self.custom_id = generate_unique_uuid(self.__class__)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.exam.title} - Question {self.order}"

class Choice(models.Model):
    custom_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200, blank=True, null=True)
    is_correct = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Always refresh custom_id if duplicate found or missing
        if self.custom_id is None or self.__class__.objects.filter(custom_id=self.custom_id).exclude(pk=self.pk).exists():
            self.custom_id = generate_unique_uuid(self.__class__)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.choice_text

class ExamAttempt(models.Model):
    custom_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.custom_id is None or self.__class__.objects.filter(custom_id=self.custom_id).exclude(pk=self.pk).exists():
            self.custom_id = generate_unique_uuid(self.__class__)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

class Answer(models.Model):
    custom_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    marks_obtained = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.custom_id is None or self.__class__.objects.filter(custom_id=self.custom_id).exclude(pk=self.pk).exists():
            self.custom_id = generate_unique_uuid(self.__class__)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Answer for {self.question.question_text[:50]}..."
