from django.contrib.auth import login as django_login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.shortcuts import render


def login(request):
    return render(request, "registration/login.html")


#TODO: make users re-sign in after page is closed
def create_account(request):
    new_user_form = UserCreationForm(request.POST)
    if new_user_form.is_valid():
        new_user_form.save()
        username = new_user_form.cleaned_data.get('username')
        password = new_user_form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        django_login(request, user)
        return redirect('index')
    return render(request, 'game/create_account.html', {'form': new_user_form})

