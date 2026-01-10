from rest_framework import viewsets
from .models import Catalogue
from .serializers import CatalogueSerializer

class CatalogueViewSet(viewsets.ModelViewSet):
    queryset = Catalogue.objects.all()
    serializer_class = CatalogueSerializer

