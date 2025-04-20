from rest_framework import viewsets
from .models import ExaminationType
from .serializers import ExaminationTypeSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class ExaminationTypeViewSet(viewsets.ModelViewSet):
    queryset = ExaminationType.objects.filter(is_deleted=False)  # Exclude deleted items
    serializer_class = ExaminationTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_destroy(self, instance):
        # Soft delete by setting `is_deleted` to True
        instance.is_deleted = True
        instance.save()