from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Author, LibraryCollection, Publisher, Book, Member
from .serializers import AuthorSerializer, LibraryCollectionSerializer, PublisherSerializer, BookSerializer, MemberSerializer
from .paginations import CustomPagination

# NOTE: none of the ViewSets below declared permission_classes, which used to
# mean they inherited DRF's own default (AllowAny) and were reachable by
# anyone on the internet with no authentication. The project now sets
# DEFAULT_PERMISSION_CLASSES = [IsAuthenticated] globally (see nkowebe/
# settings.py), so these are no longer open even without the explicit
# declarations below — but the declarations are kept explicit anyway so this
# file's access rules don't silently change if the global default ever does.


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

class MemberViewSet(viewsets.ModelViewSet):
    """
    Member records include personal contact details (address, phone_number).
    Previously any authenticated user could list every member's record, not
    just their own. Non-staff users are now restricted to their own record,
    matching the pattern used by CustomUserViewSet in the account app.
    """
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Member.objects.all()
        return Member.objects.filter(user=user)


class LibraryCollectionViewSet(viewsets.ModelViewSet):
    """
    Previously get_queryset() had its logic backwards: authenticated users
    were scoped to their own collections, but *unauthenticated* users fell
    through to `LibraryCollection.objects.all()` — returning every user's
    private collections to anyone who wasn't even logged in. The model
    already has a `visibility` field (public/private/unlisted) that this
    view never consulted. Now: a user sees their own collections plus any
    other user's PUBLIC collections, and the owner is always forced to the
    requesting user on create (rather than trusting a client-supplied value).
    """
    serializer_class = LibraryCollectionSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return LibraryCollection.objects.filter(
            Q(owner=user) | Q(visibility=LibraryCollection.PUBLIC)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

# --- Recently Added Books ViewSet ---
class RecentlyAddedBookViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing recently added books (most recent first).
    """
    queryset = Book.objects.order_by('-id')  # Default sorted by most recently added
    serializer_class = BookSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]
