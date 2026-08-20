"""
WebSocket authentication for Channels, using the project's existing DRF
auth-token scheme instead of Django session cookies.

Why this exists: the frontend is a separate-origin SPA that authenticates
every REST call with an `Authorization: Token <key>` header (see
account/views.py LoginViewSet / RegisterViewSet, and settings.py
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']). A browser's native
WebSocket API cannot set custom headers on the handshake request, and the
frontend does not use Django session cookies at all — so Channels' stock
`channels.auth.AuthMiddlewareStack` (which resolves scope['user'] from the
session cookie) never had anything to authenticate with. Every WebSocket
connection therefore reached consumers with `scope['user']` as
AnonymousUser, and the original consumers (chat_app.consumers.ChatConsumer,
classroom_app.classchat.consumers.ChatConsumer) worked around this by
trusting a client-supplied `sender_id`/`from_user_id`/`user_id` field in
each message instead — which let any connected client impersonate any
other user. See the fixes in those two consumers.py files.

This middleware gives consumers a real, server-verified `scope['user']` by
reading the same token from a `?token=<key>` query parameter on the
WebSocket URL (the only place a browser WebSocket client can attach it).
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _get_user_from_token(token_key):
    from rest_framework.authtoken.models import Token

    try:
        return Token.objects.select_related('user').get(key=token_key).user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware:
    """ASGI middleware that resolves scope['user'] from a `?token=` query
    param using DRF's Token model. Falls back to AnonymousUser when the
    token is missing or invalid — callers (consumers) are responsible for
    rejecting unauthenticated/unauthorized connections themselves."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        token_key = parse_qs(query_string).get('token', [None])[0]

        scope = dict(scope)
        scope['user'] = (
            await _get_user_from_token(token_key) if token_key else AnonymousUser()
        )
        return await self.inner(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(inner)
