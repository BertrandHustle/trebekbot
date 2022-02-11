from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/demultiplexer/(?P<room_name>\w+)/$', consumers.GameDemultiplexer.as_asgi()),
]