
from django.db import models
import uuid



class InstitutionType(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)  # Flag to mark the examination type as deleted
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name