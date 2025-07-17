from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from clubs.models import Club, ClubUserConnector
from .models import InterviewQuestion, UserInterviewProgress, InterviewSession
from .utils import transcribe_audio_file
import random
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.
@login_required
def club_prep(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    
    # Get all questions for this club
    questions = InterviewQuestion.objects.filter(club_connections__club=club)

    # Pagination setup
    page = request.GET.get('page', 1)
    paginator = Paginator(questions, 10)  # 10 questions per page
    try:
        questions_page = paginator.page(page)
    except PageNotAnInteger:
        questions_page = paginator.page(1)
    except EmptyPage:
        questions_page = paginator.page(paginator.num_pages)

    #Update prep count for club
    club_prep = ClubUserConnector.objects.get(club=club, user=request.user)
    club_prep.started_prep = True
    club_prep.save()
    
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
        'questions': questions,  # keep for now for compatibility
        'questions_page': questions_page,  # new paginated object
        'user_progress': user_progress,
        'total_questions': total_questions,
        'attempted_questions': attempted_questions,
        'completed_questions': completed_questions,
        'recent_sessions': recent_sessions,
    }

    # HTMX support: return only the questions list partial if HX-Request header is present
    if request.headers.get('HX-Request') == 'true':
        return render(request, 'interviews/_questions_list.html', context)

    return render(request, 'interviews/prep.html', context)

@login_required
def start_practice_session(request, club_id):
    """Create a new practice session with 5 unattempted questions"""
    club = get_object_or_404(Club, id=club_id)
    
    # Get all questions for this club
    all_questions = InterviewQuestion.objects.filter(club_connections__club=club)
    
    # Get questions the user hasn't attempted yet
    attempted_question_ids = UserInterviewProgress.objects.filter(
        user=request.user,
        question__in=all_questions,
        club=club,
        attempted=True
    ).values_list('question_id', flat=True)
    
    unattempted_questions = all_questions.exclude(id__in=attempted_question_ids)
    
    # Select 5 random unattempted questions (or all if less than 5)
    session_questions = list(unattempted_questions)
    if len(session_questions) >= 5:
        session_questions = random.sample(session_questions, 5)
    
    if not session_questions:
        messages.warning(request, 'No unattempted questions available for this club.')
        return redirect('clubs:prep', club_id=club_id)
    
    # Create the session
    session = InterviewSession.objects.create(
        user=request.user,
        club=club,
        category=club.category,
        questions=[q.id for q in session_questions], #creating a list of question IDs and not the actual questions
        question_count=len(session_questions),
        time_limit_minutes=30,  
    )
    
    messages.success(request, f'Practice session started with {len(session_questions)} questions!')
    return redirect('clubs:practice_session', club_id=club_id, session_id=session.id)

@login_required
def practice_session(request, club_id, session_id):
    """Handle the practice session interface"""
    club = get_object_or_404(Club, id=club_id)
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    
    # Get current question: STRICTLY ERROR CHECKING (SHOULD NEVER REACH THIS STATE)
    current_question = session.get_current_question()
    if not current_question:
        messages.error(request, 'No questions found in this session.')
        return redirect('clubs:prep', club_id=club_id)
    
    # Get or create progress for current question
    question_progress, created = UserInterviewProgress.objects.get_or_create(
        user=request.user,
        question=current_question,
        club=club,
        defaults={'attempted': True}
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'save_answer':
            # Save the current answer
            user_answer = request.POST.get('user_answer', '').strip()
            notes = request.POST.get('notes', '').strip()
            
            # Handle audio file processing
            if 'response_audio' in request.FILES:
                audio_file = request.FILES['response_audio']
                transcription_result = transcribe_audio_file(audio_file)
                
                if transcription_result['success']:
                    transcribed_text = transcription_result['text'].strip()
                    if transcribed_text:
                        user_answer = transcribed_text
                        messages.success(request, 'Audio successfully transcribed!')
                    else:
                        messages.warning(request, 'Audio transcribed but no text was detected.')
                else:
                    if not user_answer:
                        user_answer = "[Audio transcription failed]"
                    messages.error(request, f'Transcription failed: {transcription_result["error"]}')
            
            question_progress.user_answer = user_answer
            question_progress.completed = True
            question_progress.notes = notes
            question_progress.save()
            
            messages.success(request, 'Answer saved!')
            
        elif action == 'next_question':
            # Move to next question
            if session.can_move_to_next():
                session.current_question_index += 1
                session.save()
                messages.info(request, 'Moving to next question...')
            else:
                # Session completed
                session.is_completed = True
                session.completed_at = timezone.now()
                session.save()
                messages.success(request, 'Session completed!')
                return redirect('clubs:prep', club_id=club_id)
                
        elif action == 'previous_question':
            # Move to previous question
            if session.can_move_to_previous():
                session.current_question_index -= 1
                session.save()
                messages.info(request, 'Moving to previous question...')
            else:
                messages.warning(request, 'Already at the first question.')
    
    # Reload current question after navigation
    current_question = session.get_current_question()
    if not current_question:
        messages.error(request, 'No questions found in this session.')
        return redirect('clubs:prep', club_id=club_id)
    
    # Get or create progress for current question
    question_progress, created = UserInterviewProgress.objects.get_or_create(
        user=request.user,
        question=current_question,
        club=club,
        defaults={'attempted': True}
    )
    
    # Get all questions in session for navigation
    session_questions = []
    for question_id in session.questions:
        try:
            question = InterviewQuestion.objects.get(id=question_id)
            session_questions.append(question)
        except InterviewQuestion.DoesNotExist:
            pass
    
    context = {
        'club': club,
        'session': session,
        'current_question': current_question,
        'question_progress': question_progress,
        'session_questions': session_questions,
        'current_question_number': session.current_question_index + 1,
        'total_questions': len(session.questions),
    }
    
    return render(request, 'interviews/practice_session.html', context)

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
        
        # Handle audio file processing (if provided)
        if 'response_audio' in request.FILES:
            audio_file = request.FILES['response_audio']
            
            # Transcribe the audio using AssemblyAI
            transcription_result = transcribe_audio_file(audio_file)
            
            if transcription_result['success']:
                # Use the transcribed text as the answer
                transcribed_text = transcription_result['text'].strip()
                if transcribed_text:
                    user_answer = transcribed_text
                    messages.success(request, 'Audio successfully transcribed!')
                else:
                    messages.warning(request, 'Audio transcribed but no text was detected.')
            else:
                # Transcription failed, use text answer if provided
                if not user_answer:
                    user_answer = "[Audio transcription failed]"
                messages.error(request, f'Transcription failed: {transcription_result["error"]}')
        
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