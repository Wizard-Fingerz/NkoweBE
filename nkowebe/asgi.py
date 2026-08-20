"""
ASGI config for nkowebe project.

Exposes the ASGI callable as a module-level variable named ``application``.
Production runs this directly via Daphne (see PROCFILE:
`daphne -b 0.0.0.0 -p $PORT nkowebe.asgi:application`).
"""
import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nkowebe.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from classroom_app.routings import websocket_urlpatterns as classroom_ws
from chat_app.routing import websocket_urlpatterns as chat_ws
from nkowebe.channels_auth import TokenAuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # AllowedHostsOriginValidator checks the WebSocket handshake's Origin
    # header against ALLOWED_HOSTS, closing the connection if it doesn't
    # match. Without it, any website can open a cross-origin WebSocket to
    # this server from a visitor's browser (cross-site WebSocket
    # hijacking) — this was present in an old, dead, commented-out version
    # of this file but missing from the version that was actually active.
    #
    # TokenAuthMiddlewareStack resolves scope['user'] from the same
    # Authorization-token scheme used by the REST API (see
    # nkowebe/channels_auth.py for why session-based AuthMiddlewareStack
    # doesn't work for this frontend).
    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddlewareStack(
            URLRouter(
                classroom_ws + chat_ws
            )
        )
    ),
})
