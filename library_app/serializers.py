from rest_framework import serializers
from .models import Author, Publisher, Book, Member, LibraryCollection

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = [
            'id',
            'first_name',
            'last_name',
            'dob',
            'biography',
        ]

class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = [
            'id',
            'name',
            'address',
            'website',
        ]

class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    genre = serializers.StringRelatedField(many=True, read_only=True)
    uploaded_by = serializers.StringRelatedField(read_only=True)
    institution = serializers.StringRelatedField(read_only=True)
    catalogue = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'authors',
            'publisher',
            'publication_date',
            'isbn',
            'genre',
            'description',
            'total_copies',
            'available_copies',
            'file',
            'uploaded_by',
            'institution',
            'catalogue',
        ]

class MemberSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    institution = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Member
        fields = [
            'id',
            'user',
            'address',
            'phone_number',
            'joined_date',
            'is_active',
            'institution',
        ]

class LibraryCollectionSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    books = BookSerializer(many=True, read_only=True)

    class Meta:
        model = LibraryCollection
        fields = [
            'id',
            'name',
            'description',
            'owner',
            'books',
            'created_at',
        ]