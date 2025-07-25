from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from clubs.models import ClubUserConnector

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('users:profile')
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
            return redirect('users:profile')
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
    interested_clubs = ClubUserConnector.objects.filter(
        user=request.user,
        interested=True
    ).select_related('club')

    prep_clubs_count = ClubUserConnector.objects.filter(
        user=request.user,
        started_prep=True
    ).count()
    
    context = {
        'interested_clubs': interested_clubs,
        'prep_clubs_count': prep_clubs_count,
    }
    return render(request, 'users/profile.html', context)

