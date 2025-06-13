from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db import IntegrityError

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('main:home')
        else:
            context = {'error': True}
            return render(request, 'users/login.html', context)
    
    return render(request, 'users/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('main:home')
        except IntegrityError:
            context = {'error': True}
            return render(request, 'users/register.html', context)
    return render(request, 'users/register.html')

