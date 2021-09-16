from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import UserInfo

def index(request):
    return render(request, 'user/index.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return render(request, 'router/index.html')
        else:
            return HttpResponseForbidden('wrong username or password')
        
    return render(request, 'user/login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        starting_capital = request.POST['starting_capital']
        user = User.objects.create_user(username, password = password)
        user.save()
        user_info = UserInfo(user=user, starting_capital=starting_capital)
        user_info.save()

        # Log the registered user in
        login(request, user)

        return render(request, 'router/index.html')

    return render(request, 'user/register.html')
        