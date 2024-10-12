# serializers.py
from rest_framework import serializers
from .models import MailTemplate

class MailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailTemplate
        fields = ['id', 'name', 'subject', 'body']