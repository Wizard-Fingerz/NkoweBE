from django.db import models

from account.models import InstitutionalOwner
from classroom_app.definitions.insitution_types.models import InstitutionType

# Create your models here.


class Institution(models.Model):
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
