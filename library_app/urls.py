from rest_framework import routers
from django.urls import path, include
from .views import (
    AuthorViewSet, PublisherViewSet, BookViewSet, MemberViewSet, LibraryCollectionViewSet
)
from library_app.book_loan_and_reservation.views import LoanViewSet, ReservationViewSet, FineViewSet
from library_app.catalogue.views import CatalogueViewSet

# --- Recommendations Endpoint Import and Registration ---
from library_app.recommendations.views import BookRecommendationViewSet

router = routers.DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'publishers', PublisherViewSet)
router.register(r'books', BookViewSet)
router.register(r'members', MemberViewSet)
router.register(r'collections', LibraryCollectionViewSet)
router.register(r'loans', LoanViewSet)
router.register(r'reservations', ReservationViewSet)
router.register(r'fines', FineViewSet)
router.register(r'catalogues', CatalogueViewSet)

# Register recommendations endpoints (for recommendations sub-app)
router.register(r'recommendations/bookrecommendations', BookRecommendationViewSet, basename='bookrecommendation')

urlpatterns = [
    path('', include(router.urls)),
]