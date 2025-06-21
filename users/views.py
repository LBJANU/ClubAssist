from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from clubs.models import ClubInterested

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

def logout_view(request):
    logout(request)
    return redirect('main:home')

@login_required
def profile_view(request):
    # Get all clubs the user is interested in
    interested_clubs = ClubInterested.objects.filter(
        user=request.user,
        interested=True
    ).select_related('club')
    
    context = {
        'interested_clubs': interested_clubs,
    }
    return render(request, 'users/profile.html', context)

