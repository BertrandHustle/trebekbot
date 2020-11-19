from django.urls import path

from . import views

urlpatterns = [
    path('question/', views.question),
    path('judge_answer/', views.judge_answer),
    path('new_question/', views.new_question),
]