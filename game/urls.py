from django.urls import path
from game.views.auth_views import LoginView, LogoutView
from game.views.game_views import JudgeView, QuestionView, ScoreViewSet
from game.views.page_views import index

urlpatterns = [
    path('', index, name='index'),
    # game
    path('getboard/', JudgeView.as_view(), name='judge'),
    path('judge/', JudgeView.as_view(), name='judge'),
    path('question/', QuestionView.as_view(), name='question'),
    path('topten/', ScoreViewSet.as_view({'get': 'get_top_ten'}), name='top_ten'),
    path('score/', ScoreViewSet.as_view({'get': 'get_user_score'}), name='user_score'),
    # auth
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]

