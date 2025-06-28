from django.contrib import admin
from .models import InterviewQuestion, UserInterviewProgress, InterviewSession, ClubQuestionConnector


admin.site.register(InterviewSession)   
admin.site.register(ClubQuestionConnector)

@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'question_text', 'difficulty', 'question_type', 'created_at', 'updated_at', 'is_active', 'sample_answer', 'hints', 'time_limit_minutes')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserInterviewProgress)
class UserInterviewProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'club', 'attempted', 'completed', 'score', 'time_taken_minutes', 'user_answer', 'notes', 'attempted_at', 'completed_at')
    readonly_fields = ('attempted_at', 'completed_at')
    search_fields = ('user__username', 'question__title', 'club__name')
    list_filter = ('user', 'question', 'club', 'attempted', 'completed')