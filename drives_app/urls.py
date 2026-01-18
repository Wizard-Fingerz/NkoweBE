from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DriveFolderViewSet, DriveFileViewSet

router = DefaultRouter()
router.register(r'folders', DriveFolderViewSet, basename='folder')
router.register(r'files', DriveFileViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
]
