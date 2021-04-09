from django.urls import path
from game.views import game_views, registration_views

urlpatterns = [
    path('', game_views.index, name='index'),
    # game
    path('play', game_views.play, name='play'),
    # registration
    path('create_account', registration_views.create_account, name='create_account'),
]

