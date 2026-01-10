from rest_framework import serializers
from library_app.recommendations.models import BookRecommendation
from library_app.models import Book

class BookMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'isbn']

class BookRecommendationSerializer(serializers.ModelSerializer):
    book = BookMiniSerializer(read_only=True)

    class Meta:
        model = BookRecommendation
        fields = ['id', 'user', 'book', 'score', 'created_at']
        read_only_fields = ['created_at']
