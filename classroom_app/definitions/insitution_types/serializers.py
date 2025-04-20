from rest_framework import serializers
from .models import InstitutionType

class InstitutionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionType
        fields = ['id', 'name', 'is_active', 'is_deleted', 'created_at']