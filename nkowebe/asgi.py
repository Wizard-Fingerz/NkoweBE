# import os
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.security.websocket import AllowedHostsOriginValidator
# from django.core.asgi import get_asgi_application
# import classroom_app.routings

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nkowebe.settings')

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AllowedHostsOriginValidator(
#         AuthMiddlewareStack(
#             URLRouter(
#                 classroom_app.routings.websocket_urlpatterns
#             )
#         )
#     ),
# })


import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nkowebe.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from classroom_app.routings import websocket_urlpatterns as classroom_ws
from chat_app.routing import websocket_urlpatterns as chat_ws
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            classroom_ws + chat_ws
        )
    ),
})
