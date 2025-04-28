from rest_framework import serializers
from .models import ClassroomMessage

class ClassroomMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = ClassroomMessage
        fields = ['custom_id', 'classroom', 'sender', 'sender_username', 'message', 'attachment', 'created_at']
