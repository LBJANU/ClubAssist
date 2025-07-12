import assemblyai as aai
import os
from django.conf import settings
import tempfile

def transcribe_audio_file(audio_file):
    """
    Returns:
        dict: {
            'success': bool, 
            'text': str, 
            'error': str,
            'utterances': list,  # Speech segments with timing
            'sentiment_analysis': dict,  # Overall sentiment scores
            'words': list,  # Individual words with timing
            'confidence': float,  # Overall confidence
            'audio_duration': float  # Duration in seconds
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
                'audio_duration': 0.0
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
            speech_model=aai.SpeechModel.best,
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
                'audio_duration': 0.0
            }
        
        # Extract rich data from the transcript
        # TODO: DELETE THIS I THINK BECAUSE UTTERANCE ONLY WORKS IF WE CARE ABOUT SPEAKER
        # utterances_data = []
        # if transcript.utterances:
        #     for utterance in transcript.utterances:
        #         utterance_data = {
        #             'text': utterance.text,
        #             'start': utterance.start,
        #             'end': utterance.end,
        #             'confidence': utterance.confidence,
        #             'speaker': utterance.speaker if hasattr(utterance, 'speaker') else None,
        #         }
        #         utterances_data.append(utterance_data)
        
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
        
        # Return successful transcription with rich data
        return {
            'success': True,
            'text': transcript.text,
            'error': None,
            # 'utterances': utterances_data,
            'sentiment_analysis': sentiment_data,
            'words': words_data,
            'confidence': transcript.confidence,
            'audio_duration': transcript.audio_duration
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
            'audio_duration': 0.0
        } 