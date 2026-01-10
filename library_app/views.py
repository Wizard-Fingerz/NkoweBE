from rest_framework import viewsets
from .models import Author, Publisher, Book, Member
from .serializers import AuthorSerializer, PublisherSerializer, BookSerializer, MemberSerializer
from .paginations import CustomPagination

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = CustomPagination

class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    pagination_class = CustomPagination

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    pagination_class = CustomPagination

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    pagination_class = CustomPagination