from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Loan, Reservation, Fine
from .serializers import LoanSerializer, ReservationSerializer, FineSerializer

# NOTE: none of these ViewSets declared permission_classes, so they inherited
# DRF's own default (AllowAny) and were reachable by anyone with no
# authentication — including loan/fine records tied to specific members. The
# project now sets DEFAULT_PERMISSION_CLASSES = [IsAuthenticated] globally
# (see nkowebe/settings.py), so these are no longer open by default even
# without the explicit declarations below, but each ViewSet also now scopes
# non-staff users to their own member record rather than every member's.


class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Loan.objects.all()
        return Loan.objects.filter(member__user=user)


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Reservation.objects.all()
        return Reservation.objects.filter(member__user=user)


class FineViewSet(viewsets.ModelViewSet):
    queryset = Fine.objects.all()
    serializer_class = FineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Fine.objects.all()
        return Fine.objects.filter(member__user=user)
