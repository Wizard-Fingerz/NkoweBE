from django.urls import re_path
from classroom_app.classchat import consumers

websocket_urlpatterns = [
    re_path(r'ws/classroom/(?P<classroom_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]
