from django.db import models
from account.models import CustomUser
from classroom_app.classrooms.models import Classroom
import uuid

class ClassroomMessage(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # can be a student or tutor
    message = models.TextField(blank=True)
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} in {self.classroom.name}"
