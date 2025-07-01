import assemblyai as aai
import os
from django.conf import settings
import tempfile

def transcribe_audio_file(audio_file):
    """
    Returns:
        dict: {'success': bool, 'text': str, 'error': str}
    """
    try:
        api_key = os.getenv('ASSEMBLYAI_API_KEY')
        if not api_key:
            return {
                'success': False,
                'text': '',
                'error': 'AssemblyAI API key not configured'
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
            utterances=True,
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
                'error': f'Transcription failed: {transcript.error}'
            }
        
        # Return successful transcription
        return {
            'success': True,
            'text': transcript.text,
            'error': None
        }
        # if it shits the bed, return the error
    except Exception as e:
        return {
            'success': False,
            'text': '',
            'error': f'Transcription error: {str(e)}'
        } 