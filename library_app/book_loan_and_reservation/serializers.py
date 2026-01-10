from rest_framework import serializers
from .models import Loan, Reservation, Fine

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = [
            'id',
            'book',
            'member',
            'borrowed_date',
            'due_date',
            'returned_date',
            'returned',
        ]

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            'id',
            'book',
            'member',
            'reserved_date',
            'is_active',
        ]

class FineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fine
        fields = [
            'id',
            'member',
            'amount',
            'reason',
            'date_issued',
            'paid',
        ]