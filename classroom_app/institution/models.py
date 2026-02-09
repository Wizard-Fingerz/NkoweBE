from django.db import models

from account.models import InstitutionalOwner
from classroom_app.definitions.insitution_types.models import InstitutionType
import uuid

# Create your models here.


class Institution(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, unique = True, editable=False)
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='institution_logos', blank=True)
    institution_type = models.ForeignKey(InstitutionType, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name

class JobVacancy(models.Model):
    JOB_TYPES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contract', 'Contract'),
        ('Internship', 'Internship'),
        ('Temporary', 'Temporary'),
    ]

    custom_id = models.UUIDField(default=uuid.uuid4, unique = True, editable=False)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='vacancies')
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=50, choices=JOB_TYPES)
    posted_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} at {self.institution.name}"
