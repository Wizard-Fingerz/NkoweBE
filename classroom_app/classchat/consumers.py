import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Announcement, ClassroomMessage, Classroom, Reply
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

        # Send chat history
        messages = await self.get_classroom_messages(self.classroom_id)
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages,
        }))

        # Send announcement history
        announcements = await self.get_classroom_announcements(self.classroom_id)
        await self.send(text_data=json.dumps({
            'type': 'announcement_history',
            'announcements': announcements,
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    # async def receive(self, text_data):
    #     data = json.loads(text_data)
    #     message = data['message']
       

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")  # can be 'chat', 'announcement', or 'reply'


        
        classroom = await self.get_classroom(self.classroom_id)
        sender = await self.get_user(data['sender_id'])

        print(sender)


        if message_type == "announcement":
            announcement = await self.create_announcement(
                data['message'],         # message
                data['sender_id']        # sender
            )
            print(announcement)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_announcement",
                    "announcement": {
                        "id": str(announcement.id),
                        "message": announcement.message,
                        "sender_username": announcement.sender.username,
                        "created_at": announcement.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                }
            )
        elif message_type == "reply":
            announcement_id = data["announcement_id"]
            reply = await self.create_reply(
                data["sender_id"], announcement_id, data["message"]
            )
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_reply",
                    "reply": {
                        "id": str(reply.id),
                        "announcement_id": str(reply.announcement.id),
                        "message": reply.message,
                        "sender_username": reply.sender.username,
                        "created_at": reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "attachment": reply.attachment.url if reply.attachment else None,
                    }
                }
            )
        else:
            # Fallback to default chat
            
            new_message = await self.create_message(classroom, sender, data['message'])

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data['message'],
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

    async def broadcast_announcement(self, event):
        await self.send(text_data=json.dumps({
            "type": "announcement",
            "announcement": event["announcement"]
        }))

    async def broadcast_reply(self, event):
        await self.send(text_data=json.dumps({
            "type": "reply",
            "reply": event["reply"]
        }))


    @database_sync_to_async
    def get_classroom(self, classroom_id):
        return Classroom.objects.get(custom_id=classroom_id)

    @database_sync_to_async
    def get_user(self, user_id):
        print(user_id)
        return CustomUser.objects.get(id=user_id)

    @database_sync_to_async
    def create_message(self, classroom, sender, message):
        return ClassroomMessage.objects.create(
            classroom=classroom,
            sender=sender,
            message=message
        )

    @database_sync_to_async
    def get_classroom_messages(self, classroom_id):
        classroom = Classroom.objects.get(custom_id=classroom_id)
        messages = ClassroomMessage.objects.filter(classroom=classroom).order_by('created_at')
        return [
            {
                'message': msg.message,
                'sender_username': msg.sender.username,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for msg in messages
        ]

    @database_sync_to_async
    def create_announcement(self, message, sender):
        classroom = Classroom.objects.get(custom_id=self.classroom_id)
        sender = CustomUser.objects.get(id=sender)
        return Announcement.objects.create(
            classroom=classroom,
            sender=sender,
            message=message
        )

    @database_sync_to_async
    def create_reply(self, sender_id, announcement_id, message):
        sender = CustomUser.objects.get(id=sender_id)
        announcement = Announcement.objects.get(id=announcement_id)
        return Reply.objects.create(
            announcement=announcement,
            sender=sender,
            message=message
        )

    @database_sync_to_async
    def get_classroom_announcements(self, classroom_id):
        classroom = Classroom.objects.get(custom_id=classroom_id)
        announcements = Announcement.objects.filter(classroom=classroom).order_by('-created_at')
        result = []
        for ann in announcements:
            replies = ann.replies.order_by('created_at')
            result.append({
                'id': str(ann.id),
                'message': ann.message,
                'sender_username': ann.sender.username,
                'created_at': ann.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'replies': [
                    {
                        'id': str(reply.id),
                        'announcement_id': str(reply.announcement.id),
                        'message': reply.message,
                        'sender_username': reply.sender.username,
                        'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'attachment': reply.attachment.url if reply.attachment else None,
                    }
                    for reply in replies
                ]
            })
        return result

