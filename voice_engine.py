import base64
import os
import tempfile
import logging

try:
    from gtts import gTTS
    gtts_available = True
except ImportError:
    gtts_available = False

def synthesize_speech(text: str) -> dict:
    """
    Converts text to speech (base64 audio string).
    Uses gTTS if available, otherwise falls back to a mock base64 audio stream.
    """
    if gtts_available:
        try:
            # Create a temporary file to save the synthesized mp3
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_filename = fp.name
                
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_filename)
            
            with open(temp_filename, "rb") as audio_file:
                audio_bytes = audio_file.read()
                
            os.remove(temp_filename)
            
            base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            return {
                "format": "mp3",
                "audio_base64": base64_audio,
                "engine": "gTTS (Google Text-to-Speech)"
            }
        except Exception as e:
            logging.warning(f"gTTS synthesis failed, falling back to mock: {e}")
            
    # Mock fallback (returns a tiny valid 1-second silent MP3 file in base64)
    mock_mp3_base64 = (
        "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGFtZTMuOTguNFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
        "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
        "VVVVVVVVVVVf/MUxAcAAAH0AAr0AAAM5jOczmBgADAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwM"
        "DAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMD"
        "DAwMDAwMD/8xTEJwAAAfgACvQAAAM5jOczmBgADAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA"
        "wMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAw"
        "DAwMDAwM"
    )
    return {
        "format": "mp3",
        "audio_base64": mock_mp3_base64,
        "engine": "Mock Audio Engine"
    }

def transcribe_speech(audio_base64: str) -> dict:
    """
    Transcribes base64 speech audio data to text (Speech-to-Text).
    Simulates speech transcription, returning contextually accurate text for the demo.
    """
    try:
        # Validate base64 structure
        base64.b64decode(audio_base64[:100], validate=False)
    except Exception:
        return {"error": "Invalid base64 audio payload."}
        
    # Heuristic transcription based on preset indicators
    # In a production app, this would write the bytes to disk and invoke Whisper/API
    transcription = "This is a transcribed verbal explanation of the sliding window pointer logic, verifying boundary offsets."
    
    # Check if the audio is mock or preset custom audio to align logs
    if len(audio_base64) < 1000:
        transcription = "I initialized a left pointer to zero and range loop boundary right. We insert indexes to map constraints."
        
    return {
        "transcription": transcription,
        "language": "en",
        "confidence": 0.94
    }
