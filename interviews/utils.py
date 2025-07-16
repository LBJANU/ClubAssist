import assemblyai as aai
import os
from django.conf import settings
import tempfile
import requests 

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
    
    # Calculate speaking duration and total words
    if words_data:
        first_word_time = words_data[0]['start']
        last_word_time = words_data[-1]['end'] #-1 is the last element in python, who knew
        analysis['overall_metrics']['speaking_time'] = last_word_time - first_word_time
        analysis['overall_metrics']['total_words'] = len(words_data)
        
        # Calculate words per minute
        speaking_minutes = analysis['overall_metrics']['speaking_time'] / 60.0
        if speaking_minutes > 0:
            analysis['speaking_pace']['words_per_minute'] = len(words_data) / speaking_minutes
            analysis['speaking_pace']['speaking_duration'] = analysis['overall_metrics']['speaking_time']
    
    # Analyze filler words from disfluencies
    filler_words = ['um', 'uh', 'like', 'you know', 'i mean', 'basically', 'actually', 'literally']
    filler_count = 0
    filler_frequency = {}
    
    for word in words_data:
        word_text = word['text'].lower().strip()
        if word_text in filler_words:
            filler_count += 1
            filler_frequency[word_text] = filler_frequency.get(word_text, 0) + 1
    
    analysis['filler_words']['total_count'] = filler_count
    analysis['filler_words']['common_fillers'] = filler_frequency
    
    # Calculate filler word density
    if analysis['overall_metrics']['total_words'] > 0:
        analysis['filler_words']['density'] = filler_count / analysis['overall_metrics']['total_words']
    
    # Analyze pauses between words
    pauses = []
    for i in range(1, len(words_data)):
        current_word = words_data[i]
        previous_word = words_data[i-1]
        
        pause_duration = current_word['start'] - previous_word['end']
        if pause_duration > 0.5:  # Pause longer than 0.5 seconds
            pauses.append({
                'duration': pause_duration,
                'position': i,
                'start': previous_word['end'],
                'end': current_word['start']
            })
    
    analysis['pauses']['total_pauses'] = len(pauses)
    analysis['pauses']['pause_locations'] = pauses
    
    if pauses:
        analysis['pauses']['average_pause_duration'] = sum(p['duration'] for p in pauses) / len(pauses)
        analysis['pauses']['long_pauses'] = len([p for p in pauses if p['duration'] > 2.0])
    
    # Calculate silence time
    if transcript.audio_duration and analysis['overall_metrics']['speaking_time']:
        analysis['overall_metrics']['silence_time'] = transcript.audio_duration - analysis['overall_metrics']['speaking_time']
    
    return analysis

def transcribe_audio_file(audio_file):
    """
    Returns:
        dict: {
            'success': bool, 
            'text': str, 
            'error': str,
            'sentiment_analysis': dict,  # Overall sentiment scores
            'words': list,  # Individual words with timing
            'confidence': float,  # Overall confidence
            'audio_duration': float,  # Duration in seconds
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
                'utterances': [],
                'sentiment_analysis': {},
                'words': [],
                'confidence': 0.0,
                'audio_duration': 0.0,
                'analysis': {}
            }
        
        aai.settings.api_key = api_key
        
        # False so that we can decide when to delete
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            # I guess this needs to be tempfile because assemblyai doesn't support django memory files
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Configure transcription
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best, # best defaulted, but lowk might change if expensive
            language_code="en",
            disfluencies=True,
            sentiment_analysis=True,
        )
        
        # Transcribe the audio
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(temp_file_path)
        
        # Clean up temporary file (delete ish)
        os.unlink(temp_file_path)
        
        # Check for transcription errors
        if transcript.status == "error":
            return {
                'success': False,
                'text': '',
                'error': f'Transcription failed: {transcript.error}',
                'utterances': [],
                'sentiment_analysis': {},
                'words': [],
                'confidence': 0.0,
                'audio_duration': 0.0,
                'analysis': {}
            }
        
        # Extract rich data from the transcript
        utterances_data = []
        if hasattr(transcript, 'utterances') and transcript.utterances:
            for utterance in transcript.utterances:
                utterance_data = {
                    'text': utterance.text,
                    'start': utterance.start,
                    'end': utterance.end,
                    'confidence': utterance.confidence,
                    'speaker': utterance.speaker if hasattr(utterance, 'speaker') else None,
                }
                utterances_data.append(utterance_data)
        
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
        
        
        # Extract sentiment analysis data
        sentiment_data = []
        if hasattr(transcript, 'sentiment_analysis') and transcript.sentiment_analysis:
            for sentiment_result in transcript.sentiment_analysis:
                sentiment_data.append({
                    'text': sentiment_result.text,
                    'sentiment': sentiment_result.sentiment,  # POSITIVE, NEUTRAL, or NEGATIVE
                    'confidence': sentiment_result.confidence,
                    'start': sentiment_result.start,
                    'end': sentiment_result.end
                })
        
        # Perform speech analysis
        speech_analysis = analyze_speech_metrics(transcript, words_data)
        
        # Return successful transcription with rich data
        return {
            'success': True,
            'text': transcript.text,
            'error': None,
            'utterances': utterances_data,
            'sentiment_analysis': sentiment_data,
            'words': words_data,
            'confidence': transcript.confidence,
            'audio_duration': transcript.audio_duration,
            'analysis': speech_analysis
        }
        # if it shits the bed, return the error
    except Exception as e:
        return {
            'success': False,
            'text': '',
            'error': f'Transcription error: {str(e)}',
            # 'utterances': [],
            'sentiment_analysis': {},
            'words': [],
            'confidence': 0.0,
            'audio_duration': 0.0,
            'analysis': {}
        } 
    
def feedback(question, answer):
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

    # prompt, model and more info 
    data = {
        "model": "Qwen/Qwen3-235B-A22B-fp8-tput",
        "messages": [
            {"role": "system", "content": "You are a CLUB INTERVIEWER at the University of Michigan (you are a third-year student at the school). The student you are INTERVIEWING is applying to be a member of your club (and is likely a first-year or second-year student at Umich)."},
            
            {"role": "user", "content": (f"The student has just concluded answering the following question: “{question}”\n\n"
                                         f"Their answer was the following: “{answer}”\n\n"
                                         "Pretend as if you are conducting an interview with them, providing them with feedback on their answer to that question. Be HONEST, ensuring both things they did well and things they did poorly are mentioned in your feedback. Limit your feedback to 25-50 words, no less or no more. At the end of your evaluation, provide the student with a rating (on a scale of 1 to 5) of their response, considering the following three characteristics primarily (interest, experience, and motivation) but also more subtle things such as length of response, how well their response is catered to the question, cadence/confidence, and the student’s attitude. Remember to use a conversational-formal tone when giving the student feedback.")}
        ],
        # diff model settings 
        "temperature": 0.7,
        "max_tokens": 800
    }

    response = requests.post(link, json=data, headers=headers)
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    if "</think>" in content:
        return content.split("</think>", 1)[1].strip()
    else: return content