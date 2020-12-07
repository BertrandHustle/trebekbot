from django.urls import path

from . import views

urlpatterns = [
    path('game/', views.game),
    path('judge_answer/', views.judge_answer),
    path('new_question/', views.new_question),
]