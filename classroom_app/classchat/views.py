from rest_framework import viewsets, permissions
from .models import ClassroomMessage, Announcement, Reply
from .serializers import ClassroomMessageSerializer, AnnouncementSerializer, ReplySerializer

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

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all().order_by('-created_at')
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id:
            return Announcement.objects.filter(classroom__custom_id=classroom_id).order_by('-created_at')
        return Announcement.objects.none()

class ReplyViewSet(viewsets.ModelViewSet):
    queryset = Reply.objects.all().order_by('created_at')
    serializer_class = ReplySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        announcement_id = self.request.query_params.get('announcement_id')
        if announcement_id:
            return Reply.objects.filter(announcement__id=announcement_id).order_by('created_at')
        return Reply.objects.none()
