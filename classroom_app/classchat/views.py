from rest_framework import viewsets, permissions
from .models import ClassroomMessage
from .serializers import ClassroomMessageSerializer

class ClassroomMessageViewSet(viewsets.ModelViewSet):
    queryset = ClassroomMessage.objects.all().order_by('created_at')
    serializer_class = ClassroomMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
    
    def get_queryset(self):
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id:
            return ClassroomMessage.objects.filter(classroom__custom_id=classroom_id).order_by('created_at')
        return ClassroomMessage.objects.none()
