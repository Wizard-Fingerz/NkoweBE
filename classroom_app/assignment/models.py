from django.db import models
from account.models import CustomUser
from classroom_app.classroom.models import Classroom, ClassroomTutor, ClassroomStudent


class Assignment(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete = models.CASCADE)
    title = models.CharField(max_length=255)
    total_score = models.FloatField()
    submission_deadline = models.DateTimeField()
    created_by = models.ForeignKey(ClassroomTutor, on_delete = models.CASCADE)

    def __str__(self):
        return self.title


class Question(models.Model):
    ASSIGNMENT_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('file', 'File'),
        ('date', 'Date'),
        ('time', 'Time'),
        ('select', 'Select'),
        ('radio', 'Radio'),
        ('checkbox', 'Checkbox'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="questions", null=True, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="subquestions", on_delete=models.CASCADE)

    question = models.TextField()
    type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES)
    score = models.FloatField()
    expected_answer = models.JSONField(null=True, blank=True)  # Can store string, list, or file info
    comprehension = models.TextField(blank=True, null=True)
    options = models.JSONField(blank=True, null=True)  # For select/radio/checkbox

    def __str__(self):
        return self.question


class StudentAssignment(models.Model):
    STATUS_CHOICES = [
        ("undone", "Undone"),
        ("incomplete", "Incomplete"),
        ("completed", "Completed"),
    ]

    student = models.ForeignKey(ClassroomStudent, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="undone")
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_draft = models.BooleanField(default=True)

class Answer(models.Model):
    student_assignment = models.ForeignKey(StudentAssignment, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.JSONField()