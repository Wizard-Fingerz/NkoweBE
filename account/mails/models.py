# models.py
import uuid
from django.db import models

class MailTemplate(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, unique = True, editable=False)
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name