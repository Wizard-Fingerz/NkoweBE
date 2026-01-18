from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import DriveFolder, DriveFile
from .serializers import DriveFolderSerializer, DriveFileSerializer, DriveTreeSerializer



from rest_framework import viewsets, pagination


class CustomPagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'num_pages': self.page.paginator.num_pages,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'results': data
        })


class DriveFolderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing drive folders"""
    serializer_class = DriveFolderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        return DriveFolder.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get the complete folder tree structure with pagination"""
        root_folders = DriveFolder.objects.filter(owner=request.user, parent__isnull=True).order_by('name')
        page = self.paginate_queryset(root_folders)
        if page is not None:
            serializer = DriveTreeSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = DriveTreeSerializer(root_folders, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rename(self, request, pk=None):
        """Rename a folder"""
        folder = self.get_object()
        new_name = request.data.get('name')
        if not new_name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        folder.name = new_name
        folder.save()
        serializer = self.get_serializer(folder)
        return Response(serializer.data)


class DriveFileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing drive files"""
    serializer_class = DriveFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = CustomPagination

    def get_queryset(self):
        return DriveFile.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a file to a specific folder"""
        folder_id = request.data.get('folder_id')
        file = request.FILES.get('file')
        
        if not folder_id or not file:
            return Response(
                {'error': 'folder_id and file are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        folder = get_object_or_404(DriveFolder, id=folder_id, owner=request.user)
        
        # Create the file
        drive_file = DriveFile.objects.create(
            owner=request.user,
            name=file.name,
            folder=folder,
            file=file,
            mime_type=file.content_type or ''
        )
        
        serializer = self.get_serializer(drive_file, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def rename(self, request, pk=None):
        """Rename a file"""
        file = self.get_object()
        new_name = request.data.get('name')
        if not new_name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        file.name = new_name
        file.save()
        serializer = self.get_serializer(file, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Get download URL for a file"""
        file = self.get_object()
        serializer = self.get_serializer(file, context={'request': request})
        return Response({'download_url': serializer.data['file_url']})
