from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta
from clubs.models import ClubUserConnector
from interviews.models import UserInterviewProgress
import json

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
    # Get all clubs the user is interested in (excluding hidden clubs)
    interested_clubs = ClubUserConnector.objects.filter(
        user=request.user,
        interested=True,
        club__hidden=False
    ).select_related('club')

    prep_clubs_count = ClubUserConnector.objects.filter(
        user=request.user,
        started_prep=True
    ).count()

    twenty_four_hours_ago = timezone.now() - timedelta(hours=24)

    recent_clubs = UserInterviewProgress.objects.filter(
        user=request.user,
        completed=True,
        completed_at__gte=twenty_four_hours_ago
    ).count()

    current_date = timezone.now().date()
    start_date = current_date - timedelta(days=6)

    daily_completions = UserInterviewProgress.objects.filter(
        user=request.user,
        completed=True,
        completed_at__gte=start_date,
        completed_at__lt=current_date + timedelta(days=1)
    ).annotate(
        date=TruncDate('completed_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    chart_data = {
        'labels': [],
        'data': []
    }

    while start_date <= current_date:
        chart_data['labels'].append(start_date.strftime('%Y-%m-%d'))

        count = 0
        for completion in daily_completions:
            if completion['date'] == start_date:
                count = completion['count']
                break

        chart_data['data'].append(count)
        start_date += timedelta(days=1)

    context = {
        'interested_clubs': interested_clubs,
        'prep_clubs_count': prep_clubs_count,
        'recent_clubs': recent_clubs,
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'users/profile.html', context)



