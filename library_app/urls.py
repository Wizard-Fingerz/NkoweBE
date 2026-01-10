from rest_framework import routers
from django.urls import path, include
from .views import (
    AuthorViewSet, PublisherViewSet, BookViewSet, MemberViewSet, LibraryCollectionViewSet, RecentlyAddedBookViewSet
)
from library_app.book_loan_and_reservation.views import LoanViewSet, ReservationViewSet, FineViewSet
from library_app.catalogue.views import CatalogueViewSet

# --- Recommendations Endpoint Import and Registration ---
from library_app.recommendations.views import BookRecommendationViewSet

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

urlpatterns = [
    path('', include(router.urls)),
]