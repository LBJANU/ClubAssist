from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from clubs.models import Club
from .models import InterviewQuestion, UserInterviewProgress, InterviewSession

# Create your views here.
@login_required
def club_prep(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    
    # Get all questions for this club
    questions = InterviewQuestion.objects.filter(club_connections__club=club)
    
    # Get user's progress on these questions
    user_progress = UserInterviewProgress.objects.filter(
        user=request.user,
        question__in=questions,
        club=club
    )
    
    # Calculate progress stats
    total_questions = questions.count()
    attempted_questions = user_progress.filter(attempted=True).count()
    completed_questions = user_progress.filter(completed=True).count()
    
    # Get user's recent sessions for this club
    recent_sessions = InterviewSession.objects.filter(
        user=request.user,
        club=club
    ).order_by('-started_at')[:5]

    context = {
        'club': club,
        'questions': questions,
        'user_progress': user_progress,
        'total_questions': total_questions,
        'attempted_questions': attempted_questions,
        'completed_questions': completed_questions,
        'recent_sessions': recent_sessions,
    }

    return render(request, 'interviews/prep.html', context)

@login_required
def practice_question(request, club_id, question_id):
    club = get_object_or_404(Club, id=club_id)
    question = get_object_or_404(InterviewQuestion, id=question_id)

    # we don't need to do update because if its attempted we can't "unattempt" it
    question_progress, _ = UserInterviewProgress.objects.get_or_create(
        user=request.user, 
        question=question, 
        club=club,
        defaults={'attempted': True})
    
    if request.method == 'POST':
        user_answer = request.POST.get('user_answer', '').strip()
        notes = request.POST.get('notes', '').strip()

        question_progress.user_answer = user_answer
        question_progress.completed = True
        question_progress.notes = notes

        question_progress.save()

    context = {
        'club': club,
        'question': question,
        'question_progress': question_progress,
    }
    return render(request, 'interviews/practice.html', context)