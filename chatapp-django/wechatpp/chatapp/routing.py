from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/room/(?P<room_slug>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/chatbox/$', consumers.ChatboxConsumer.as_asgi()),
]