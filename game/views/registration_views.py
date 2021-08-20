# Django
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from game.models import Player

# Project
from src.redis_interface import RedisInterface

redis_handler = RedisInterface()


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
    form = AuthenticationForm()
    return render(request, 'registration/login.html', context={'form': form})


def logout_view(request):
    logout(request)


def create_account(request):
    new_user_form = UserCreationForm(request.POST)
    if new_user_form.is_valid():
        user = new_user_form.save()
        login(request, user)
        # # get new user object
        username = new_user_form.cleaned_data.get('username')
        newly_created_user = User.objects.get(username=username)
        # # link and create new Player object
        player = Player(user=newly_created_user, name=username)
        player.save()
        return redirect('index')
    return render(request, 'game/create_account.html', {'form': new_user_form})

