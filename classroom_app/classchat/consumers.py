import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ClassroomMessage, Classroom
from account.models import CustomUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.classroom_id = self.scope['url_route']['kwargs']['classroom_id']
        self.room_group_name = f'classroom_{self.classroom_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = data['sender_id']

        # Save message to database
        classroom = await self.get_classroom(self.classroom_id)
        sender = await self.get_user(sender_id)

        new_message = ClassroomMessage.objects.create(
            classroom=classroom,
            sender=sender,
            message=message
        )

        # Broadcast message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_username': sender.username,
                'created_at': new_message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender_username = event['sender_username']
        created_at = event['created_at']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_username': sender_username,
            'created_at': created_at,
        }))

    @database_sync_to_async
    def get_classroom(self, classroom_id):
        return Classroom.objects.get(custom_id=classroom_id)

    @database_sync_to_async
    def get_user(self, user_id):
        return CustomUser.objects.get(id=user_id)
