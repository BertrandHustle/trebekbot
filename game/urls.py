from django.urls import path

from game.views import game_views

urlpatterns = [
    path('', game_views.index, name='index'),
    path('play', game_views.play, name='play')
]

