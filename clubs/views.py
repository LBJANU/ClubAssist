from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import F
from django.contrib.auth.decorators import login_required
from .models import Club, ClubUserConnector

@login_required
def club_list(request):
    #ALl passed through for the initial load
    club_categories = Club.CATEGORY_CHOICES
    clubs = Club.objects.all().order_by('name').filter(hidden=False)
    
    user_interests = {}
    if request.user.is_authenticated:
        interests = ClubUserConnector.objects.filter(
            user=request.user,
            club__in=clubs
        )
        for interest in interests:
            user_interests[interest.club_id] = interest.interested
    
    context = {
        'club_categories': club_categories,
        'clubs': clubs,
        'user_interests': user_interests,
        'selected_category': None,
        'search_query': '',
    }
    # club_categories = Club.CATEGORY_CHOICES
    
    # context = {
    #     'club_categories': club_categories,
    # }
    return render(request, 'clubs/club_list.html', context)

@login_required
def search_clubs(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    clubs = Club.objects.all().filter(hidden=False)
    
    if query:
        clubs = clubs.filter(name__icontains=query)
    
    if category:
        clubs = clubs.filter(category=category)
    
    clubs = clubs.order_by('name')
    
    # Same logic as the original view for user interests
    user_interests = {}
    if request.user.is_authenticated:
        interests = ClubUserConnector.objects.filter(
            user=request.user,
            club__in=clubs
        )
        for interest in interests:
            user_interests[interest.club_id] = interest.interested
    
    context = {
        'clubs': clubs,
        'user_interests': user_interests,
        'search_query': query,
        'selected_category': category,
    }
    
    return render(request, 'clubs/clubs_grid.html', context)

@login_required
def toggle_interest(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    
    # Try to get existing object first
    try:
        club_interested = ClubUserConnector.objects.get(club=club, user=request.user)
        new_value = not club_interested.interested
    except ClubUserConnector.DoesNotExist:
        new_value = True
    
    club_interested, created = ClubUserConnector.objects.update_or_create(
        club=club,
        user=request.user,
        defaults={'interested': new_value}
    )

    context = {
        'club': club,
        'club_interested': club_interested.interested,
    }
    return render(request, 'clubs/club_interest_button.html', context)
    
    # Return just the button content
    # icon_class = "fas fa-heart" if club_interested.interested else "far fa-heart"
    # button_text = "Interested" if club_interested.interested else "Not Interested"
    
    # return HttpResponse(
    #     f'<button class="text-blue-500 hover:text-blue-700 transition-colors">'
    #     f'<i class="{icon_class}"></i> {button_text}'
    #     f'</button>'
    # )
