from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .models import Notebook, Note, Flashcard
from .serializers import NotebookSerializer, NoteSerializer, FlashcardSerializer

class NotebookViewSet(viewsets.ModelViewSet):
    serializer_class = NotebookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        return Notebook.objects.filter(owner=self.request.user).order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content', 'tags']

    def get_queryset(self):
        # Allow filtering by notebook_id via query param
        queryset = Note.objects.filter(notebook__owner=self.request.user).order_by('-updated_at')
        notebook_id = self.request.query_params.get('notebook', None)
        if notebook_id is not None:
            queryset = queryset.filter(notebook_id=notebook_id)
        return queryset

class FlashcardViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Flashcard.objects.filter(notebook__owner=self.request.user).order_by('-created_at')
        notebook_id = self.request.query_params.get('notebook', None)
        if notebook_id is not None:
            queryset = queryset.filter(notebook_id=notebook_id)
        return queryset
