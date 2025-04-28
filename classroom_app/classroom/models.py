from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from account.models import CustomUser, Student, Tutor
from classroom_app.institution.models import Institution
from classroom_app.definitions.subjects.models import Subject
from classroom_app.definitions.examination_types.models import ExaminationType
import uuid


class Tag(models.Model):
    
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    

class Classroom(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="classroom_institution")
    tag = models.ManyToManyField(Tag)
    subject = models.ManyToManyField(Subject)
    capacity = models.IntegerField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        related_name="classroom_creator", 
        null=True, 
        blank=True
    )
    modified_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        related_name="classroom_modifier", 
        null=True, 
        blank=True
    )
    is_deleted = models.BooleanField(default=False)  # Flag to mark the classroom as deleted

    def __str__(self):
        return self.name
    
    @property
    def number_of_students(self):
        return self.classroomstudent_set.count()

class ClassroomTutor(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='tutors')
    comments = GenericRelation('Comment', related_query_name='tutor_comments')
    role = models.CharField(max_length=50, choices=[
        ('TEACHER', _('Teacher')),
        ('ASSISTANT', _('Assistant')),
    ])

    def __str__(self):
        return f"{self.tutor.username} - {self.classroom.name}"

class ClassroomStudent(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='students')
    comments = GenericRelation('Comment', related_query_name='student_comments')

    def __str__(self):
        return f"{self.student.username} - {self.classroom.name}"


class ClassroomExamination(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    examination_type = models.ForeignKey(ExaminationType, on_delete=models.CASCADE)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.examination_type.name} - {self.classroom.name}"

class ClassroomAttachment(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    file = models.FileField(upload_to='classroom_attachments/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} - {self.classroom.name}"


    
class Comment(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    creator = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Comment on {self.classroom.name} - {self.text}"
    

class ClassroomTermsAndConditions(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    classroom = models.OneToOneField(Classroom, on_delete=models.CASCADE)
    terms_and_conditions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.classroom.name} Terms and Conditions"