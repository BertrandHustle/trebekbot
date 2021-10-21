from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/answer/$', consumers.AnswerConsumer.as_asgi()),
    re_path(r'ws/game/timer/$', consumers.TimerConsumer.as_asgi()),
    re_path(r'ws/game/question/$', consumers.QuestionConsumer.as_asgi()),
    re_path(r'ws/game/buzzer/$', consumers.BuzzerConsumer.as_asgi()),
]