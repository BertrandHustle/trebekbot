from django.shortcuts import render
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect


def login(request):
    return render(request, "accounts/login.html")


def create_account(request):
    new_user_form = UserCreationForm(request.POST)
    if new_user_form.is_valid():
        new_user_form.save()
        username = new_user_form.cleaned_data.get('username')
        password = new_user_form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('index')
    return render(request, 'accounts/create_account.html', {'form', new_user_form})

