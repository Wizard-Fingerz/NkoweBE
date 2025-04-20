from rest_framework import viewsets
from .models import InstitutionType
from .serializers import InstitutionTypeSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class InstitutionTypeViewSet(viewsets.ModelViewSet):
    queryset = InstitutionType.objects.filter(is_deleted=False)  # Exclude deleted items
    serializer_class = InstitutionTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_destroy(self, instance):
        # Soft delete by setting `is_deleted` to True
        instance.is_deleted = True
        instance.save()