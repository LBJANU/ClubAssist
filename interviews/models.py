from django.db import models
from django.contrib.auth.models import User
from clubs.models import Club

class InterviewQuestion(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    QUESTION_TYPE_CHOICES = [
        ('behavioral', 'Behavioral'),
        ('technical', 'Technical'),
        ('case_study', 'Case Study'),
        ('brain_teaser', 'Brain Teaser'),
        ('general', 'General'),
    ]
    
    # Basic question info
    title = models.CharField(max_length=200)
    question_text = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='general')
    
    # Optional fields for different question types
    sample_answer = models.TextField(blank=True, null=True)
    hints = models.TextField(blank=True, null=True)
    time_limit_minutes = models.IntegerField(default=5, help_text="Suggested time limit in minutes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['difficulty', 'created_at']
    
    def __str__(self):
        return f"{self.title} ({self.difficulty})"

class ClubQuestionConnector(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='question_connections')
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE, related_name='club_connections')
    
    class Meta:
        unique_together = ('club', 'question')
    
    def __str__(self):
        return f"{self.club.name} - {self.question.title}"
    

# no foreign key to club because this checks how a User did on a specific question. Club FK could make this messy esp if it relates to more than one club
class UserInterviewProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interview_progress')
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE, related_name='user_attempts')
    
    # Progress tracking
    attempted = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True, help_text="Score out of 100")
    time_taken_minutes = models.FloatField(null=True, blank=True)
    
    # User's response
    user_answer = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, help_text="User's notes about their performance")
    
    # Timestamps
    attempted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'question')
        ordering = ['-attempted_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.question.title}"

# keep foreign key to club because this is a session that a user does for a club. Club intent is must. 
class InterviewSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interview_sessions')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='interview_sessions', null=True, blank=True)
    category = models.CharField(max_length=20, choices=Club.CATEGORY_CHOICES)
    
    # Session settings
    difficulty = models.CharField(max_length=10, choices=InterviewQuestion.DIFFICULTY_CHOICES, default='medium')
    question_count = models.IntegerField(default=5)
    time_limit_minutes = models.IntegerField(default=30)
    
    # Session progress
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Results
    total_score = models.IntegerField(null=True, blank=True)
    questions_attempted = models.IntegerField(default=0)
    questions_correct = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.category} Session ({self.started_at.date()})"
