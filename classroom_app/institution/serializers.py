from rest_framework import serializers

from classroom_app.institution.models import Institution, InstitutionType



class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = "__all__"
        
class InstitutionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionType
        fields = "__all__"
        