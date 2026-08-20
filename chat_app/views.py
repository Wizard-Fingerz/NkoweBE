from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ChatRoom, Message, FriendRequest
from .serializers import ChatRoomSerializer, MessageSerializer, FriendRequestSerializer
from rest_framework.authentication import TokenAuthentication
from django.db import models
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
# Create your views here.

class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    ChatRoomSerializer nests both `participants` and every `message` in the
    room, and this ViewSet had no get_queryset override — so `GET
    /chat-rooms/` and `/chat-rooms/<id>/` returned EVERY chat room in the
    system, participants and full message contents included, to any
    authenticated user. Scoped to rooms the requester is actually a
    participant of.
    """
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return ChatRoom.objects.filter(participants=self.request.user)

    @action(detail=False, methods=['get'], url_path='my-room')
    def my_room(self, request):
        user = request.user
        room = ChatRoom.objects.filter(participants=user).first()
        if room:
            serializer = self.get_serializer(room)
            return Response({'room_id': room.id, 'room': serializer.data})
        return Response({'detail': 'No room found for user.'}, status=404)

class MessageViewSet(viewsets.ModelViewSet):
    """
    Had no get_queryset override, so `GET /chat-messages/` returned every
    message from every room in the system to any authenticated user —
    private conversation contents readable by anyone with an account.
    Scoped to messages in rooms the requester is a participant of.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return Message.objects.filter(room__participants=self.request.user)

class FriendRequestViewSet(viewsets.ModelViewSet):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return FriendRequest.objects.filter(models.Q(from_user=user) | models.Q(to_user=user))

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        friend_request = self.get_object()
        if friend_request.to_user != request.user:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        friend_request.status = 'accepted'
        friend_request.save()
        return Response({'status': 'accepted'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        friend_request = self.get_object()
        if friend_request.to_user != request.user:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        friend_request.status = 'rejected'
        friend_request.save()
        return Response({'status': 'rejected'})
