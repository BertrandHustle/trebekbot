from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('game/', views.game),
    path('judge_answer/', views.judge_answer),
    path('new_question/', views.new_question),
    path('accounts/', include('django.contrib.auth.urls')),
    re_path(r"^signup/", views.signup)
]