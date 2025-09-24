import assemblyai as aai
import os
from django.conf import settings
import tempfile
import requests
import re 

def analyze_speech_metrics(transcript, words_data):
    """
    Analyze speech patterns from transcript data.
    
    Returns:
        dict: Analysis metrics including filler words, pauses, speaking pace
    """
    analysis = {
        'filler_words': {
            'total_count': 0,
            'words_per_minute': 0,
            'common_fillers': {},
            'density': 0.0
        },
        'pauses': {
            'total_pauses': 0,
            'long_pauses': 0,  # >2.0 seconds
            'average_pause_duration': 0.0,
            'pause_locations': []
        },
        'speaking_pace': {
            'words_per_minute': 0,
            'speaking_duration': 0.0,
            'pace_consistency': 'unknown'
        },
        'overall_metrics': {
            'total_words': 0,
            'speaking_time': 0.0,
            'silence_time': 0.0
        }
    }
    
    if not words_data:
        return analysis
    
    if words_data:
        # AssemblyAI returns timestamps in milliseconds, convert to seconds for calculations
        first_word_time = words_data[0]['start'] / 1000.0
        last_word_time = words_data[-1]['end'] / 1000.0 #-1 is the last element in python, who knew
        analysis['overall_metrics']['speaking_time'] = last_word_time - first_word_time
        analysis['overall_metrics']['total_words'] = len(words_data)
        
        # Calculate words per minute
        speaking_minutes = analysis['overall_metrics']['speaking_time'] / 60.0
        if speaking_minutes > 0:
            analysis['speaking_pace']['words_per_minute'] = len(words_data) / speaking_minutes
            analysis['speaking_pace']['speaking_duration'] = analysis['overall_metrics']['speaking_time']
    
    filler_words = ['um', 'uh', 'like', 'you know', 'i mean', 'basically', 'actually', 'literally']
    filler_count = 0
    filler_frequency = {}
    
    for word in words_data:
        word_text = word['text'].lower().strip().rstrip(',.!?;:')
        if word_text in filler_words:
            filler_count += 1
            filler_frequency[word_text] = filler_frequency.get(word_text, 0) + 1
            print(f"FOUND FILLER: '{word['text']}' -> '{word_text}'")
        else:
            print(f"NOT FILLER: '{word['text']}' -> '{word_text}'")
    
    analysis['filler_words']['total_count'] = filler_count
    analysis['filler_words']['common_fillers'] = filler_frequency
    
    if analysis['overall_metrics']['total_words'] > 0:
        analysis['filler_words']['density'] = filler_count / analysis['overall_metrics']['total_words']
    
    pauses = []
    for i in range(1, len(words_data)):
        current_word = words_data[i]
        previous_word = words_data[i-1]
        
        pause_duration = (current_word['start'] - previous_word['end']) / 1000.0
        if pause_duration > 0.5: 
            pauses.append({
                'duration': pause_duration,
                'position': i,
                'start': previous_word['end'] / 1000.0,
                'end': current_word['start'] / 1000.0
            })
    

    
    analysis['pauses']['total_pauses'] = len(pauses)
    analysis['pauses']['pause_locations'] = pauses
    
    if pauses:
        analysis['pauses']['average_pause_duration'] = sum(p['duration'] for p in pauses) / len(pauses)
        analysis['pauses']['long_pauses'] = len([p for p in pauses if p['duration'] > 2.0])
    else:
        analysis['pauses']['average_pause_duration'] = 0.0
        analysis['pauses']['long_pauses'] = 0
    
    audio_duration = transcript.audio_duration
    speaking_time = analysis['overall_metrics']['speaking_time']
    analysis['overall_metrics']['silence_time'] = max(0, audio_duration - speaking_time)
    
    return analysis

def transcribe_audio_file(audio_file):
    """
    Returns:
        dict: {
            'success': bool, 
            'text': str, 
            'error': str,
            'analysis': dict,  # Enhanced analysis metrics -> using words data and transcription for metrics.
        }
    """
    try:
        api_key = os.getenv('ASSEMBLYAI_API_KEY')
        if not api_key:
            return {
                'success': False,
                'text': '',
                'error': 'AssemblyAI API key not configured',
                'analysis': {}
            }
        
        aai.settings.api_key = api_key
        
        # False so that we can decide when to delete
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            # I guess this needs to be tempfile because assemblyai doesn't support django memory files
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best, 
            language_code="en",
            disfluencies=True,
        )
        
        # Transcribe the audio
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(temp_file_path)
        
        os.unlink(temp_file_path)
        
        if transcript.status == "error":
            return {
                'success': False,
                'text': '',
                'error': f'Transcription failed: {transcript.error}',
                'analysis': {}
            }
        
        words_data = []
        if hasattr(transcript, 'words') and transcript.words:
            for word in transcript.words:
                words_data.append({
                    'text': word.text,
                    'start': word.start,
                    'end': word.end,
                    'confidence': word.confidence,
                    'speaker': word.speaker if hasattr(word, 'speaker') else None
                })
        
        
        speech_analysis = analyze_speech_metrics(transcript, words_data)
        
        return {
            'success': True,
            'text': transcript.text,
            'error': None,
            'analysis': speech_analysis
        }
        # if it shits the bed, return the error
    except Exception as e:
        return {
            'success': False,
            'text': '',
            'error': f'Transcription error: {str(e)}',
            'analysis': {}
        } 
    
def feedback(question, answer, category, speech_metrics = None, case_context = None):
    """
    Provides feedback on student's given answer to given question, taking into account speech metrics.

    Returns: 
        dict: {
            'display_text': str,  # Formatted feedback + rating for user display
            'feedback': str,       # Just the feedback text
            'rating': float        # Rating as number for database storage
        }
    """
    # getting api key from .env; for production swap to access from settings.py
    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key: raise ValueError("can't find API key")
    
    # url for together api
    link = "https://api.together.xyz/v1/chat/completions"
    
    # headers for the request 
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Build context section conditionally cuz only on case study
    context_section = ""
    if case_context and case_context.strip():
        context_section = f"\nCase Context:\n{case_context.strip()}\n"

    # speech metrics 
    cScore = -1
    if speech_metrics:
        f = speech_metrics['filler_words']['density'] * 100
        if f <= 5: filler = 5
        elif f <= 10: filler = 4
        elif f <= 15: filler = 3
        elif f <= 20: filler = 2
        else: filler = 1
        print("Filler Word Count: ", speech_metrics['filler_words']['total_count'])
        print("Total Words: ", speech_metrics['overall_metrics']['total_words'])
        print(f"Filler: {filler}")
        print(f"Filler density: {f}")
        
        lp = speech_metrics['pauses']['long_pauses']
        avg_p = speech_metrics['pauses']['average_pause_duration']
        if lp <= 2 and avg_p < 1.2: pause = 5
        elif lp <= 4: pause = 4
        elif lp <= 6: pause = 3
        elif lp <= 8: pause = 2
        else: pause = 1 
        
        print(f"Pause: {pause}")
        print(f"Long pauses: {lp}")
        print(f"Average pause duration: {avg_p}")

        wpm = speech_metrics['speaking_pace']['words_per_minute']
        if 110 <= wpm <= 160: pace = 5
        elif 90 <= wpm < 110 or 160 < wpm <= 180: pace = 4
        elif 75 <= wpm < 90 or 180 < wpm <= 200: pace = 3
        elif 60 <= wpm < 75 or 200 < wpm <= 220: pace = 2
        else: pace = 1
        
        print(f"Pace: {pace}")
        print(f"Words per minute: {wpm}")

        st = speech_metrics['overall_metrics']['speaking_time']
        si = speech_metrics['overall_metrics']['silence_time']
        ratio = st / (st + si) if st + si > 0 else 0
        if 0.65 <= ratio <= 0.92: silence = 5
        elif 0.60 <= ratio < 0.65 or 0.92 < ratio <= 0.95: silence = 4
        elif 0.55 <= ratio < 0.60 or 0.95 < ratio <= 0.97: silence = 3
        else: silence = 1.5
        
        print(f"Silence: {silence}")
        print(f"Speaking time: {st}")
        print(f"Silence time: {si}")
        print(f"Ratio: {ratio}")

        cScore = round(((filler + pause + pace + silence) / 4), 1)

    if 0 <= cScore and cScore <= 5:
        prompt = (
            f"The student has just concluded answering the following question: '{question}'{context_section}\n"
            f"Their answer was the following: '{answer}'\n\n"
            f"Additionally, consider the following confidence score: {cScore}\n\n"
            "Pretend as if you are conducting an interview with them, providing them with feedback on their answer to that question. "
            "Be HONEST, ensuring both things they did well and things they did poorly are mentioned in your feedback. "
            "Limit your feedback to 50-75 words, no less or no more. Do not include extensive internal reasoning. If you must think, be brief. "
            "Limit thinking to under 200 tokens. At the end of your evaluation, provide the student with a rating (on a scale of 1 to 5, including decimals) of their response, "
            "considering the following three characteristics primarily (interest, experience, and motivation) but also more subtle things such as length of response, "
            "how well their response is catered to the question, cadence/confidence, and the student’s attitude. "
            "IF the confidence score provided is in the 1-5 scale, then in your rating, ensure you take a weighted average of two numbers, "
            "the student's confidence score (30%) and their response's score for purely content. "
            "IF the confidence score is not between 1 and 5, simply ignore it and rate the content of their response. "
            "Remember to use a conversational-formal tone when giving the student feedback. "
            "Do NOT use stars or emojis. Do NOT mention that you are using a weighted average. Do NOT be excessively nice or sugarcoat negative feedback."
        )

    else: # any other case just pretend there's no cScore 
        prompt = (
            f"The student has just concluded answering the following question: '{question}'{context_section}\n"
            f"Their answer was the following: '{answer}'\n\n"
            "Pretend as if you are conducting an interview with them, providing them with feedback on their answer to that question. "
            "Be HONEST, ensuring both things they did well and things they did poorly are mentioned in your feedback. "
            "Limit your feedback to 50-75 words, no less or no more. Do not include extensive internal reasoning. If you must think, be brief. "
            "Limit thinking to under 200 tokens. At the end of your evaluation, provide the student with a rating (on a scale of 1 to 5, including decimals) of their response, "
            "considering the following three characteristics primarily (interest, experience, and motivation) but also more subtle things such as length of response, "
            "how well their response is catered to the question, cadence/confidence, and the student’s attitude. "
            "Ignore the confidence score. Remember to use a conversational-formal tone when giving the student feedback. "
            "Do NOT use stars or emojis. Do NOT be excessively nice or sugarcoat negative feedback."
        )

    # prompt, model and more info 
    data = {
        "model": "Qwen/Qwen3-235B-A22B-fp8-tput",
        "messages": [
            {"role": "system", "content": f"You are a {category.upper()} CLUB INTERVIEWER at the University of Michigan (you are a third-year student at the school)."
                                          "The student you are INTERVIEWING is applying to be a member of your club (and is likely a first-year or second-year student at Umich)."
                                          "You will respond to each question with a JSON object containing two fields:\n\n"
                                            "1. 'feedback': a string containing concise, honest feedback (25-50 words), noting both strengths and weaknesses.\n"
                                            "2. 'rating': a string representing a score from 1.0 to 5.0 (decimals allowed), based on interest, experience, motivation, and presentation quality.\n\n"
                                            "Do not include any commentary outside the JSON object. Do not use stars, emojis, or extra words. Only return the JSON."},
            
            {"role": "user", "content": prompt}
        ],
        # diff model settings 
        "temperature": 0.7,
        "max_tokens": 600
    }

    # Debug: You can check out the payload being sent to LLM. 
    print("=" * 80)
    print("LLM PAYLOAD DEBUG:")
    print("=" * 80)
    print(f"Category: {category}")
    print(f"System Message: {data['messages'][0]['content']}")
    print(f"User Message: {data['messages'][1]['content']}")
    print("=" * 80)

    response = requests.post(link, json=data, headers=headers)
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    content = re.sub(r"</?think>", "", content)

    try:
        import json
        parsed_response = json.loads(content.strip())
        
        # Extract feedback and rating
        feedback_text = parsed_response.get('feedback', 'No feedback provided.')
        rating_str = parsed_response.get('rating', '0.0')
        
        # Convert rating to float, with fallback
        try:
            rating = float(rating_str)
        except (ValueError, TypeError):
            rating = 0.0
        
        return {
            'display_text': f"{feedback_text}\n\nRating: {rating}/5",
            'feedback': feedback_text,
            'rating': rating
        }
        
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails - return the raw content as feedback
        return {
            'display_text': f"{content.strip()}\n\nRating: 0.0/5",
            'feedback': content.strip(),
            'rating': 0.0
        }
