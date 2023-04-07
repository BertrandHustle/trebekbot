from django.urls import path
from game.views.auth_views import LoginView, LogoutView
from game.views.game_views import JudgeView, QuestionView
from game.views.page_views import index

urlpatterns = [
    path('', index, name='index'),
    # game
    path('question', QuestionView.as_view(), name='question'),
    path('judge', JudgeView.as_view(), name='judge'),
    # auth
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]

