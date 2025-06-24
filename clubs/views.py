from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import F
from django.contrib.auth.decorators import login_required
from .models import Club, ClubUserConnector

# Create your views here.
@login_required
def club_list(request):
    category = request.GET.get('category')
    clubs = Club.objects.all()
    
    if category:
        clubs = clubs.filter(category=category)
    
    clubs = clubs.order_by('name')
    club_categories = Club.CATEGORY_CHOICES
    
    # Initialize empty dictionary
    user_interests = {}
    
    # not sure if user actually needs to be authenticated to see the list (security check tho)
    if request.user.is_authenticated:
        # Get all interests for this user and these clubs
        interests = ClubUserConnector.objects.filter(
            user=request.user,
            club__in=clubs
        )
        
        # Store just the interested boolean value, not the whole object
        for interest in interests:
            user_interests[interest.club_id] = interest.interested

    context = {
        'clubs': clubs,
        'club_categories': club_categories,
        'selected_category': category,
        'user_interests': user_interests,
    }
    return render(request, 'clubs/club_list.html', context)

@login_required
def toggle_interest(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    
    # Try to get existing object first
    try:
        club_interested = ClubUserConnector.objects.get(club=club, user=request.user)
        # Toggle existing value
        new_value = not club_interested.interested
    except ClubUserConnector.DoesNotExist:
        # Create new with default True
        new_value = True
    
    # Use update_or_create with the calculated value
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
