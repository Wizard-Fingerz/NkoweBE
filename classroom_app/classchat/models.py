from django.db import models
from account.models import CustomUser
from classroom_app.classroom.models import Classroom
import uuid

class Reply(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)
    announcement = models.ForeignKey('Announcement', on_delete=models.CASCADE, related_name='replies')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    attachment = models.FileField(upload_to='reply_attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.sender.username} to {self.announcement.id}"

class ClassroomMessage(models.Model):
    custom_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # can be a student or tutor
    message = models.TextField(blank=True)
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sender.username} in {self.classroom.name}"


class Announcement(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="announcements")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # replies: related_name on Reply