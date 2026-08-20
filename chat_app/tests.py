"""
Regression tests for the Week 1-2 security stabilization pass on chat_app.

These exercise the fixes made to chat_app/views.py (the REST endpoints;
the WebSocket consumer fix in chat_app/consumers.py is covered separately
since it isn't reachable through APITestCase's HTTP test client):
  - ChatRoomViewSet.get_queryset now scopes results to rooms the requester
    actually participates in. It previously had no get_queryset override at
    all, so `GET /chat-rooms/` returned every chat room in the system —
    participant lists and full message contents included — to any
    authenticated user;
  - MessageViewSet.get_queryset now scopes results to messages in rooms the
    requester participates in, for the same reason;
  - FriendRequestViewSet.get_queryset scopes results to requests where the
    requester is either the sender or the recipient.

Written but not yet run from this environment (no reachable Django/Python
execution environment — see the project's migration/CI notes). Please run
`python manage.py test chat_app` locally and report back any failures.
"""
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from account.models import CustomUser
from chat_app.models import ChatRoom, FriendRequest, Message


def make_user(username, **extra):
    return CustomUser.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='not-a-real-password-123',
        **extra,
    )


class ChatRoomScopingTests(APITestCase):
    def setUp(self):
        self.alice = make_user('alice_chat')
        self.bob = make_user('bob_chat')
        self.carol = make_user('carol_chat')
        self.alice_bob_room = ChatRoom.objects.create(name='Alice & Bob')
        self.alice_bob_room.participants.set([self.alice, self.bob])
        self.bob_carol_room = ChatRoom.objects.create(name='Bob & Carol')
        self.bob_carol_room.participants.set([self.bob, self.carol])

    def test_anonymous_request_is_rejected(self):
        response = self.client.get(reverse('api:chatroom-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_user_sees_only_rooms_they_participate_in(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(reverse('api:chatroom-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row['id'] for row in response.data], [self.alice_bob_room.pk])

    def test_user_not_in_any_room_sees_nothing(self):
        outsider = make_user('outsider_chat')
        self.client.force_authenticate(user=outsider)
        response = self.client.get(reverse('api:chatroom-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class MessageScopingTests(APITestCase):
    def setUp(self):
        self.alice = make_user('alice_msg')
        self.bob = make_user('bob_msg')
        self.carol = make_user('carol_msg')
        self.alice_bob_room = ChatRoom.objects.create(name='Alice & Bob')
        self.alice_bob_room.participants.set([self.alice, self.bob])
        self.bob_carol_room = ChatRoom.objects.create(name='Bob & Carol')
        self.bob_carol_room.participants.set([self.bob, self.carol])
        self.alice_bob_message = Message.objects.create(room=self.alice_bob_room, sender=self.alice, content='hi bob')
        self.bob_carol_message = Message.objects.create(room=self.bob_carol_room, sender=self.bob, content='hi carol')

    def test_anonymous_request_is_rejected(self):
        response = self.client.get(reverse('api:message-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_user_sees_only_messages_in_their_own_rooms(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(reverse('api:message-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row['id'] for row in response.data], [self.alice_bob_message.pk])

    def test_shared_participant_sees_messages_from_both_their_rooms(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(reverse('api:message-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {row['id'] for row in response.data}
        self.assertEqual(returned_ids, {self.alice_bob_message.pk, self.bob_carol_message.pk})


class FriendRequestScopingTests(APITestCase):
    def setUp(self):
        self.alice = make_user('alice_fr')
        self.bob = make_user('bob_fr')
        self.carol = make_user('carol_fr')
        self.alice_to_bob = FriendRequest.objects.create(from_user=self.alice, to_user=self.bob)
        self.bob_to_carol = FriendRequest.objects.create(from_user=self.bob, to_user=self.carol)

    def test_user_sees_only_friend_requests_involving_them(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(reverse('api:friendrequest-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row['id'] for row in response.data], [self.alice_to_bob.pk])

    def test_recipient_also_sees_the_request(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(reverse('api:friendrequest-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {row['id'] for row in response.data}
        self.assertEqual(returned_ids, {self.alice_to_bob.pk, self.bob_to_carol.pk})

    def test_uninvolved_user_sees_nothing(self):
        outsider = make_user('outsider_fr')
        self.client.force_authenticate(user=outsider)
        response = self.client.get(reverse('api:friendrequest-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
