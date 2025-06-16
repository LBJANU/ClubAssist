from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path('', views.club_list, name='club_list'),
    path('toggle-interest/<int:club_id>/', views.toggle_interest, name='toggle_interest'),
] 