from rest_framework import viewsets
from .models import Author, LibraryCollection, Publisher, Book, Member
from .serializers import AuthorSerializer, LibraryCollectionSerializer, PublisherSerializer, BookSerializer, MemberSerializer
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


class LibraryCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = LibraryCollectionSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return LibraryCollection.objects.filter(owner=user)
        return LibraryCollection.objects.none()

# --- Recently Added Books ViewSet ---
class RecentlyAddedBookViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing recently added books (most recent first).
    """
    queryset = Book.objects.order_by('-id')  # Default sorted by most recently added
    serializer_class = BookSerializer
    pagination_class = CustomPagination