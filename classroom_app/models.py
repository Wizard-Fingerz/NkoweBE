from django.db import models

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

class Subject(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ])
    category = models.CharField(max_length=20, choices=[
        ('STEM', 'STEM'),
        ('Humanities', 'Humanities'),
        ('Languages', 'Languages'),
    ])
    icon = models.ImageField(upload_to='subject_icons', blank=True)

    def __str__(self):
        return self.name
    
