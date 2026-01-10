from rest_framework import routers
from django.urls import path, include
from .views import AuthorViewSet, PublisherViewSet, BookViewSet, MemberViewSet
from library_app.book_loan_and_reservation.views import LoanViewSet, ReservationViewSet, FineViewSet
from library_app.catalogue.views import CatalogueViewSet

router = routers.DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'publishers', PublisherViewSet)
router.register(r'books', BookViewSet)
router.register(r'members', MemberViewSet)
router.register(r'loans', LoanViewSet)
router.register(r'reservations', ReservationViewSet)
router.register(r'fines', FineViewSet)
router.register(r'catalogues', CatalogueViewSet)

urlpatterns = [
    path('', include(router.urls)),
]