from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from rest_framework.authentication import TokenAuthentication

from rest_framework.permissions import IsAuthenticated
# Create your views here.

class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'], url_path='my-room')
    def my_room(self, request):
        user = request.user
        room = ChatRoom.objects.filter(participants=user).first()
        if room:
            serializer = self.get_serializer(room)
            return Response({'room_id': room.id, 'room': serializer.data})
        return Response({'detail': 'No room found for user.'}, status=404)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
