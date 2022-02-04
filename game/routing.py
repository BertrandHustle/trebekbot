from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/demultiplexer/(?P<room_name>\w+)/$', consumers.GameDemultiplexer.as_asgi()),
    re_path(r'ws/game/answer/(?P<room_name>\w+)/$', consumers.AnswerConsumer.as_asgi()),
    re_path(r'ws/game/question/(?P<room_name>\w+)/$', consumers.QuestionConsumer.as_asgi()),
    re_path(r'ws/game/buzzer/(?P<room_name>\w+)/$', consumers.BuzzerConsumer.as_asgi()),
]