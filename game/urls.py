from django.urls import path
from game.views import game_views, account_views

urlpatterns = [
    path('', game_views.index, name='index'),
    # game
    path('play', game_views.play, name='play'),
    # registration
    path('create_account', account_views.create_account, name='create_account'),
]

