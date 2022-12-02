from django.urls import path
from game.views import page_views, registration_views
from game.views.game_views import JudgeView, QuestionView

urlpatterns = [
    path('', page_views.index, name='index'),
    # game
    path('question', QuestionView.as_view(), name='question'),
    path('judge', JudgeView.as_view(), name='judge'),
    # path('play/<str:room_name>/', page_views.play, name='play'),
    # registration
    path('login', registration_views.login_view, name='login'),
    path('logout', registration_views.logout_view, name='logout'),
    path('create_account', registration_views.create_account, name='create_account'),
]

