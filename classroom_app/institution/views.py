from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from classroom_app.institution.models import Institution
from classroom_app.institution.serializers import InstitutionSerializer
# Create your views here.



class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
