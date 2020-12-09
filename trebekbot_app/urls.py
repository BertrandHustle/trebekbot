from django.urls import path, include
from . import views

urlpatterns = [
    path('game/', views.game),
    path('judge_answer/', views.judge_answer),
    path('new_question/', views.new_question),
    path('accounts/', include('django.contrib.auth.urls')),
]