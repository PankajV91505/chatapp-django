from django.urls import re_path
from chatapp.consumers import ChatConsumer, InboxConsumer

websocket_urlpatterns = [
    re_path(r'^ws/(?P<room_slug>[^/]+)/$', ChatConsumer.as_asgi()),
    re_path(r'^ws/inbox/$', InboxConsumer.as_asgi()),
]