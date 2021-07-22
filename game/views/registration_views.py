# Django
from django.contrib.auth import login as django_login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.shortcuts import render
from game.models import Player

# Project
from src.redis_interface import RedisInterface

redis_handler = RedisInterface()


def login(request):
    return render(request, "registration/login.html")


def logout_view(request):
    logout(request)


def create_account(request):
    new_user_form = UserCreationForm(request.POST)
    if new_user_form.is_valid():
        user = new_user_form.save()
        django_login(request, user)
        # # get new user object
        username = new_user_form.cleaned_data.get('username')
        newly_created_user = User.objects.get(username=username)
        # # link and create new Player object
        player = Player(user=newly_created_user, name=username)
        player.save()
        return redirect('index')
    return render(request, 'game/create_account.html', {'form': new_user_form})

