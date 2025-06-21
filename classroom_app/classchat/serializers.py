from rest_framework import serializers
from .models import ClassroomMessage, Announcement, Reply

class ClassroomMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = ClassroomMessage
        fields = ['custom_id', 'classroom', 'sender', 'sender_username', 'message', 'attachment', 'created_at']

class AnnouncementSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'classroom', 'sender', 'sender_username', 'message', 'created_at']

class ReplySerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Reply
        fields = ['id', 'announcement', 'sender', 'sender_username', 'message', 'attachment', 'created_at']
