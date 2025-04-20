from rest_framework import serializers
from .models import ExaminationType


class ExaminationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExaminationType
        fields = ['id', 'name', 'description', 'region',
                  'level', 'is_active', 'is_deleted', 'created_at']
