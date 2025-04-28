from django.contrib.auth.models import AbstractUser , Group, Permission
from django.db import models
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from account.definitions.models import Title
from classroom_app.definitions.subjects.models import Subject
# from classroom_app.institution.models import Institution
import uuid


class UserType(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    STUDENT = 'student', 'Student'
    INSTITUTION_OWNER = 'institution_owner', 'Institution Owner'
    TUTOR = 'tutor', 'Tutor'
    MODERATOR = 'moderator', 'Moderator'
    TEACHER = 'teacher', 'Teacher'
    COUNSELOR = 'counselor', 'Counselor'
    ADMINISTRATOR = 'administrator', 'Administrator'
    LIBRARIAN = 'librarian', 'Librarian'
    IT_STAFF = 'it_staff', 'IT Staff'
    ALUMNI = 'alumni', 'Alumni'
    GUEST_LECTURER = 'guest_lecturer', 'Guest Lecturer'
    MENTOR = 'mentor', 'Mentor'
    RESEARCH_PARTNER = 'research_partner', 'Research Partner'
    GOVERNMENT_AGENCY = 'government_agency', 'Government Agency'
  
    OTHER = 'other', 'Other'


class CustomUser(AbstractUser):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=[(choice.value, choice.name) for choice in UserType], default=UserType.OTHER.value)
    email = models.EmailField(unique=True)
    
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

class Admin(models.Model):
    user = models.OneToOneField(CustomUser , on_delete=models.CASCADE, primary_key=True)
    # Add any additional admin-specific fields here

class Student(models.Model):
    user = models.OneToOneField(CustomUser , on_delete=models.CASCADE, primary_key=True)
    date_of_birth = models.DateField(null=True, blank=True)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    address = models.TextField()
    parent = models.ForeignKey('Parent', on_delete=models.CASCADE, null=True, blank=True)
    parent_permission = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='student_profiles')
    grade_level = models.CharField(max_length=20, choices=[
        ('Elementary', 'Elementary'),
        ('Middle School', 'Middle School'),
        ('High School', 'High School'),
        ('College', 'College'),
    ])
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)
    subjects_of_interest = models.ManyToManyField(Subject, blank=True)

    # def __str__(self):
    #     return self.user.username
    
class Parent(models.Model):
    user = models.OneToOneField(CustomUser , on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    relationship = models.CharField(max_length=20, choices=[
        ('Mother', 'Mother'),
        ('Father', 'Father'),
        ('Guardian', 'Guardian'),
    ])
    emergency_contact = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class InstitutionalOwner(models.Model):
    user = models.OneToOneField(CustomUser , on_delete=models.CASCADE, primary_key=True)
    institution = models.ForeignKey('classroom_app.Institution', on_delete=models.CASCADE, related_name="insitution_in_institution_owner")
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.institution.name} - {self.title.name}"
    
class Tutor(models.Model):
    user = models.OneToOneField(CustomUser , on_delete=models.CASCADE, primary_key=True)
    date_of_birth = models.DateField(null=True, blank=True)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True, related_name="insitution_in_tutor")
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    address = models.TextField()
    qualification = models.CharField(max_length=255)
    experience = models.TextField()
    subjects = models.ManyToManyField(Subject)  # assuming you have a Subject model
    description = models.TextField()
    availability = models.TextField()
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    profile_picture = models.ImageField(upload_to='tutor_profiles')
    background_check = models.TextField()
    references = models.TextField()


    
class Moderator(models.Model):
    user = models.OneToOneField(CustomUser , on_delete=models.CASCADE, primary_key=True)
    # Add any additional moderator-specific fields here

class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    subject_specialization = models.CharField(max_length=255)
    experience = models.TextField()
    qualifications = models.CharField(max_length=255)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username

class Counselor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    specialization = models.CharField(max_length=255)
    experience = models.TextField()
    qualifications = models.CharField(max_length=255)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username

class Administrator(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    role = models.CharField(max_length=255)
    experience = models.TextField()
    qualifications = models.CharField(max_length=255)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username

class Librarian(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    experience = models.TextField()
    qualifications = models.CharField(max_length=255)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username

class ITStaff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    role = models.CharField(max_length=255)
    experience = models.TextField()
    qualifications = models.CharField(max_length=255)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username

class Alumni(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    graduation_year = models.DateField()
    degree = models.CharField(max_length=255)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username

class GuestLecturer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    subject_specialization = models.CharField(max_length=255)
    experience = models.TextField()
    qualifications = models.CharField(max_length=255)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username

class Mentor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    experience = models.TextField()
    qualifications = models.CharField(max_length=255)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username

class ResearchPartner(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    organization = models.CharField(max_length=255)
    research_interests = models.TextField()
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username

class GovernmentAgency(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    agency_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    institutions = models.ManyToManyField('classroom_app.Institution', blank=True)

    def __str__(self):
        return self.user.username