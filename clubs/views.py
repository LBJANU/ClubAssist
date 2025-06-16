from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Club

# Create your views here.

def club_list(request):
    category = request.GET.get('category')
    clubs = Club.objects.all()
    
    if category:
        clubs = clubs.filter(category=category)
    
    clubs = clubs.order_by('name')
    club_categories = Club.CATEGORY_CHOICES
    
    context = {
        'clubs': clubs,
        'club_categories': club_categories,
        'selected_category': category,
    }
    return render(request, 'clubs/club_list.html', context)

def toggle_interest(request, club_id):
    if not request.user.is_authenticated:
        return HttpResponse('Please log in to mark clubs as interesting', status=401)
    
    club = get_object_or_404(Club, id=club_id)
    # Here you would implement the logic to toggle interest
    # For example, using a through model or a many-to-many relationship
    
    # For now, we'll just return a simple response
    return HttpResponse(
        f'<button class="text-blue-500 hover:text-blue-700 transition-colors" '
        f'hx-post="{club_id}" hx-swap="outerHTML">'
        f'<i class="fas fa-heart"></i> Interested'
        f'</button>'
    )
