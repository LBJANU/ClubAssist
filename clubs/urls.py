from django.urls import path
from . import views
from interviews.views import club_prep, practice_question, start_practice_session, practice_session, practice_session_summary

app_name = 'clubs'

urlpatterns = [
    path('', views.club_list, name='club_list'),
    path('toggle-interest/<int:club_id>/', views.toggle_interest, name='toggle_interest'),
    path('prep/<int:club_id>/', club_prep, name='prep'),
    path('practice/<int:club_id>/<int:question_id>/', practice_question, name='practice_question'),
    path('session/start/<int:club_id>/', start_practice_session, name='start_practice_session'),
    path('session/<int:club_id>/<int:session_id>/', practice_session, name='practice_session'),
    path('session/<int:session_id>/summary/', practice_session_summary, name='practice_session_summary'),
] 