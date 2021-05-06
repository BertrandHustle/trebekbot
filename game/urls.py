from django.urls import path
from game.views import game_views, registration_views

urlpatterns = [
    path('', game_views.index, name='index'),
    # game
    path('play', game_views.play, name='play'),
    path('new_question', game_views.new_question, name='new_question'),
    path('judge_answer', game_views.judge_answer, name='judge_answer'),
    # registration
    path('create_account', registration_views.create_account, name='create_account'),
]

