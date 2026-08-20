from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from library_app.paginations import CustomPagination
from .models import Catalogue
from .serializers import CatalogueSerializer

class CatalogueViewSet(viewsets.ModelViewSet):
    # Was fully open (no permission_classes).
    queryset = Catalogue.objects.all()
    serializer_class = CatalogueSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]
