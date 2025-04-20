
from django.db import models



class ExaminationType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=100)  # e.g., Secondary, Vocational
    region = models.CharField(max_length=100)  # e.g., Nigeria, Global
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)  # Flag to mark the examination type as deleted
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name