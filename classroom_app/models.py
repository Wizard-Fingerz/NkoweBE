from django.db import models

# Create your models here.



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
    
