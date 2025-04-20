from django.db import models

from account.models import InstitutionalOwner

# Create your models here.

class InstitutionType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

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
