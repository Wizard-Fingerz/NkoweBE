from rest_framework import routers
from django.urls import path, include

from .views import (
    AuthorViewSet,
    PublisherViewSet,
    BookViewSet,
    MemberViewSet,
    LibraryCollectionViewSet,
    RecentlyAddedBookViewSet,
)

from library_app.book_loan_and_reservation.views import LoanViewSet, ReservationViewSet, FineViewSet
from library_app.catalogue.views import CatalogueViewSet
from library_app.recommendations.views import BookRecommendationViewSet

# --- Discussion endpoints ---
from library_app.discussion.views import (
    DiscussionThreadViewSet,
    DiscussionPostViewSet,
    DiscussionThreadReadStatusViewSet,
)

router = routers.DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(r'books', BookViewSet, basename='book')
router.register(r'members', MemberViewSet, basename='member')
router.register(r'collections', LibraryCollectionViewSet, basename='librarycollection')
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'fines', FineViewSet, basename='fine')
router.register(r'catalogues', CatalogueViewSet, basename='catalogue')
router.register(r'recommendations/bookrecommendations', BookRecommendationViewSet, basename='bookrecommendation')
router.register(r'recently-added-books', RecentlyAddedBookViewSet, basename='recentlyaddedbook')

# Discussion endpoints
router.register(r'discussion/threads', DiscussionThreadViewSet, basename='discussionthread')
router.register(r'discussion/posts', DiscussionPostViewSet, basename='discussionpost')
router.register(r'discussion/thread-read-statuses', DiscussionThreadReadStatusViewSet, basename='discussionthreadreadstatus')

urlpatterns = [
    path('', include(router.urls)),
]