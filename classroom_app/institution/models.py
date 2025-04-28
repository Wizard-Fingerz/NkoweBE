from django.db import models

from account.models import InstitutionalOwner
from classroom_app.definitions.insitution_types.models import InstitutionType
import uuid

# Create your models here.


class Institution(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
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
