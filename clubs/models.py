from django.db import models
from django.contrib.auth.models import User

class Club(models.Model):

    CATEGORY_CHOICES = [
        ('tech', 'Technology'),
        ('business', 'Business'),
        ('pre-med', 'Pre-Med'),
        ('pre-dental', 'Pre-Dental'),
        ('arts', 'Arts'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ClubUserConnector(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='seen_clubs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seen_clubs')
    seen_at = models.DateTimeField(auto_now_add=True)
    interested = models.BooleanField(default=False)
    started_prep = models.BooleanField(default=False)

    class Meta:
        unique_together = ('club', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.club.name} (Interested: {self.interested}, Started Prep: {self.started_prep})"
