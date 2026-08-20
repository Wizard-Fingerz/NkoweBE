import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, FriendRequest
from account.models import CustomUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']
        self.user_group_name = None
        self.joined_room_group = False

        # SECURITY: previously any WebSocket connection — authenticated or
        # not — was accepted and joined to room_group_name for whatever
        # room_id the client requested, with no check that the connecting
        # user was actually a participant of that room. That let anyone
        # read another room's full chat history and live messages simply by
        # connecting to its room_id. Both checks below are new.
        if not self.user.is_authenticated:
            await self.close()
            return

        is_participant = await self.is_room_participant(self.room_id, self.user)
        if not is_participant:
            await self.close()
            return

        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        self.joined_room_group = True
        await self.accept()

        # Send chat history
        messages = await self.get_room_messages(self.room_id)
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages,
        }))

    async def disconnect(self, close_code):
        if self.joined_room_group:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        if self.user_group_name:
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # SECURITY: every branch below used to take the acting user's ID
        # (sender_id / from_user_id / user_id) directly from client-supplied
        # JSON instead of the authenticated connection (self.user). Any
        # connected client could send messages, create/accept/reject friend
        # requests, or read a friend list AS ANY OTHER USER simply by
        # putting a different ID in the payload — a full authorization
        # bypass that also sidestepped the ownership checks already present
        # in the REST FriendRequestViewSet (accept/reject requiring
        # to_user == request.user). Every "which user is acting" value below
        # now comes from self.user, never from client input.
        data = json.loads(text_data)
        msg_type = data.get('type', 'chat')
        if msg_type == 'chat':
            content = data['content']
            sender = self.user
            room = await self.get_room(self.room_id)
            message = await self.create_message(room, sender, content)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'sender_username': sender.username,
                        'content': message.content,
                        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                }
            )
        elif msg_type == 'friend_request':
            from_user_id = self.user.id
            to_user_id = data['to_user_id']
            friend_request = await self.create_friend_request(from_user_id, to_user_id)
            # Notify the recipient
            await self.channel_layer.group_send(
                f'user_{to_user_id}',
                {
                    'type': 'friend_request_notification',
                    'friend_request': {
                        'id': friend_request.id,
                        'from_user_id': from_user_id,
                        'to_user_id': to_user_id,
                        'status': friend_request.status,
                        'created_at': friend_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                }
            )
        elif msg_type == 'friend_accept':
            request_id = data['request_id']
            friend_request = await self.accept_friend_request(request_id, self.user.id)
            if friend_request is None:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'detail': 'Not allowed to accept this friend request.',
                }))
                return
            # Notify both users
            await self.channel_layer.group_send(
                f'user_{friend_request.from_user.id}',
                {
                    'type': 'friend_accept_notification',
                    'friend_request': {
                        'id': friend_request.id,
                        'from_user_id': friend_request.from_user.id,
                        'to_user_id': friend_request.to_user.id,
                        'status': friend_request.status,
                        'created_at': friend_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                }
            )
            await self.channel_layer.group_send(
                f'user_{friend_request.to_user.id}',
                {
                    'type': 'friend_accept_notification',
                    'friend_request': {
                        'id': friend_request.id,
                        'from_user_id': friend_request.from_user.id,
                        'to_user_id': friend_request.to_user.id,
                        'status': friend_request.status,
                        'created_at': friend_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                }
            )
        elif msg_type == 'friend_reject':
            request_id = data['request_id']
            friend_request = await self.reject_friend_request(request_id, self.user.id)
            if friend_request is None:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'detail': 'Not allowed to reject this friend request.',
                }))
                return
            # Notify the sender
            await self.channel_layer.group_send(
                f'user_{friend_request.from_user.id}',
                {
                    'type': 'friend_reject_notification',
                    'friend_request': {
                        'id': friend_request.id,
                        'from_user_id': friend_request.from_user.id,
                        'to_user_id': friend_request.to_user.id,
                        'status': friend_request.status,
                        'created_at': friend_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                }
            )
        elif msg_type == 'friend_list':
            friends = await self.get_friends(self.user.id)
            await self.send(text_data=json.dumps({
                'type': 'friend_list',
                'friends': friends,
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message']
        }))

    async def friend_request_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'friend_request',
            'friend_request': event['friend_request']
        }))

    async def friend_accept_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'friend_accept',
            'friend_request': event['friend_request']
        }))

    async def friend_reject_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'friend_reject',
            'friend_request': event['friend_request']
        }))

    @database_sync_to_async
    def is_room_participant(self, room_id, user):
        return ChatRoom.objects.filter(id=room_id, participants=user).exists()

    @database_sync_to_async
    def get_room(self, room_id):
        return ChatRoom.objects.get(id=room_id)

    @database_sync_to_async
    def get_user(self, user_id):
        return CustomUser.objects.get(id=user_id)

    @database_sync_to_async
    def create_message(self, room, sender, content):
        return Message.objects.create(room=room, sender=sender, content=content)

    @database_sync_to_async
    def get_room_messages(self, room_id):
        room = ChatRoom.objects.get(id=room_id)
        messages = Message.objects.filter(room=room).order_by('timestamp')
        return [
            {
                'id': msg.id,
                'sender_username': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for msg in messages
        ]

    @database_sync_to_async
    def create_friend_request(self, from_user_id, to_user_id):
        from_user = CustomUser.objects.get(id=from_user_id)
        to_user = CustomUser.objects.get(id=to_user_id)
        friend_request, _ = FriendRequest.objects.get_or_create(
            from_user=from_user, to_user=to_user, status='pending'
        )
        return friend_request

    @database_sync_to_async
    def accept_friend_request(self, request_id, acting_user_id):
        """Returns None (instead of raising) if the acting user isn't the
        request's recipient — mirrors the check already enforced by
        FriendRequestViewSet.accept() over REST."""
        friend_request = FriendRequest.objects.get(id=request_id)
        if friend_request.to_user_id != acting_user_id:
            return None
        friend_request.status = 'accepted'
        friend_request.save()
        return friend_request

    @database_sync_to_async
    def reject_friend_request(self, request_id, acting_user_id):
        """Returns None (instead of raising) if the acting user isn't the
        request's recipient — mirrors the check already enforced by
        FriendRequestViewSet.reject() over REST."""
        friend_request = FriendRequest.objects.get(id=request_id)
        if friend_request.to_user_id != acting_user_id:
            return None
        friend_request.status = 'rejected'
        friend_request.save()
        return friend_request

    @database_sync_to_async
    def get_friends(self, user_id):
        user = CustomUser.objects.get(id=user_id)
        # Friends are users with accepted requests either sent or received
        sent = FriendRequest.objects.filter(from_user=user, status='accepted').values_list('to_user__id', 'to_user__username')
        received = FriendRequest.objects.filter(to_user=user, status='accepted').values_list('from_user__id', 'from_user__username')
        friends = list(sent) + list(received)
        return [{'id': f[0], 'username': f[1]} for f in friends] 