from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, MessageViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'chat-rooms', ChatRoomViewSet, basename='chatroom')
router.register(r'chat-messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
] 