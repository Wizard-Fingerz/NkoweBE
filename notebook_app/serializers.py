from rest_framework import serializers
from .models import Notebook, Note, Flashcard

class NotebookSerializer(serializers.ModelSerializer):
    note_count = serializers.IntegerField(source='notes.count', read_only=True)
    flashcard_count = serializers.IntegerField(source='flashcards.count', read_only=True)

    class Meta:
        model = Notebook
        fields = ['id', 'owner', 'title', 'description', 'created_at', 'updated_at', 'note_count', 'flashcard_count']
        read_only_fields = ['owner', 'created_at', 'updated_at']

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'notebook', 'title', 'content', 'tags', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ['id', 'notebook', 'front', 'back', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
