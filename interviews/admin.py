from django.contrib import admin
from .models import InterviewQuestion, UserInterviewProgress, InterviewSession, ClubQuestionConnector

admin.site.register(InterviewQuestion)
admin.site.register(UserInterviewProgress)
admin.site.register(InterviewSession)   
admin.site.register(ClubQuestionConnector)
