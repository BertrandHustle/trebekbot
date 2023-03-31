from django.urls import path
from game.views.auth_views import LoginView
from game.views.game_views import JudgeView, QuestionView
from game.views.page_views import index

urlpatterns = [
    path('', index, name='index'),
    # game
    path('question', QuestionView.as_view(), name='question'),
    path('judge', JudgeView.as_view(), name='judge'),
    # auth
    # path('csrf/', get_csrf, name='api-csrf'),
    path('login/', LoginView.as_view(), name='login'),
    # path('logout/', logout_view, name='api-logout'),
    # path('session/', SessionView.as_view(), name='session'),
    # path('get-username/', GetUsername.as_view(), name='get-username'),
]

