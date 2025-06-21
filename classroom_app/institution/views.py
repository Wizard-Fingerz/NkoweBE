from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from classroom_app.institution.models import Institution
from classroom_app.institution.serializers import InstitutionSerializer
from account.models import InstitutionalOwner, Tutor, Teacher, Counselor, Administrator, Librarian, ITStaff, Alumni, GuestLecturer, Mentor, ResearchPartner, GovernmentAgency, Title
from django.db.models import Q
# Create your views here.



class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        # Institutions where user is the creator (InstitutionalOwner)
        owner_institutions = Institution.objects.filter(insitution_in_institution_owner__user=user)
        # Institutions where user is staff (tutor, teacher, etc)
        staff_institutions = Institution.objects.filter(
            Q(insitution_in_tutor__user=user) |
            Q(teacher__user=user) |
            Q(counselor__user=user) |
            Q(administrator__user=user) |
            Q(librarian__user=user) |
            Q(itstaff__user=user) |
            Q(alumni__user=user) |
            Q(guestlecturer__user=user) |
            Q(mentor__user=user) |
            Q(researchpartner__user=user) |
            Q(governmentagency__user=user)
        )
        # Union and distinct
        return (owner_institutions | staff_institutions).distinct()

    def perform_create(self, serializer):
        institution = serializer.save()
        user = self.request.user
        # Use a default Title if not provided
        # title = Title.objects.first()  # You may want to customize this
        InstitutionalOwner.objects.create(user=user, institution=institution, phone=user.email, email=user.email)
