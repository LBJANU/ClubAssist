from django.urls import path
from . import views
from interviews.views import club_prep

app_name = 'clubs'

urlpatterns = [
    path('', views.club_list, name='club_list'),
    path('toggle-interest/<int:club_id>/', views.toggle_interest, name='toggle_interest'),
    path('prep/<int:club_id>/', club_prep, name='prep'),
] 