"""
Speech Service module for Day 12 AI Application
Handles speech-to-text conversion using OpenAI Whisper API
"""
import os
import re
import logging
import tempfile
from typing import Dict, Any
from openai import OpenAI

# Module logger
logger = logging.getLogger(__name__)

# OpenAI client (will be set by app.py)
client = None


def clean_transcription(text: str) -> str:
    """
    Clean up common Whisper API artifacts and noise

    Args:
        text: Raw transcription text

    Returns:
        str: Cleaned text
    """
    # Remove common Whisper artifacts
    artifacts = [
        r'Transcribed by https://otter\.ai',
        r'Transcribed by otter\.ai',
        r'Thank you for watching!?',
        r'Thanks for watching!?',
        r'Subscribe to my channel',
        r'\[BLANK_AUDIO\]',
        r'\[MUSIC\]',
        r'\[NOISE\]',
        r'you\.{3,}',  # "you..." (common false positive)
    ]

    cleaned = text
    for pattern in artifacts:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # If cleaned text is empty or just "you", return empty
    if cleaned.lower() in ['you', 'yeah', 'uh', 'um', '']:
        logger.warning(f"⚠️ Detected likely artifact: '{text}' → returning empty")
        return ''

    return cleaned


def transcribe_audio(audio_file, language: str = None) -> Dict[str, Any]:
    """
    Transcribe audio file to text using OpenAI Whisper API

    Args:
        audio_file: Audio file object (FileStorage from Flask)
        language: Optional language code (e.g., 'en', 'uk', 'ru')

    Returns:
        dict: Transcription result with text and metadata
    """
    if not client:
        raise ValueError("OpenAI client not initialized")

    try:
        logger.info(f"🎤 Starting audio transcription (language: {language or 'auto'})")

        # Save uploaded file to temporary location
        # Whisper API requires a file path or file object
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name

        logger.info(f"📁 Saved audio to temp file: {temp_path}")

        try:
            # Open the saved file and send to Whisper API
            with open(temp_path, 'rb') as audio:
                # Call Whisper API
                transcription_params = {
                    "model": "whisper-1",
                    "file": audio,
                    "response_format": "verbose_json",  # Get detailed response with metadata
                    "prompt": "This audio contains numbers, calculations, definitions, or commands. Transcribe accurately including all digits and technical terms."  # Help Whisper recognize numbers
                }

                # Add language if specified
                if language:
                    transcription_params["language"] = language

                transcript = client.audio.transcriptions.create(**transcription_params)

            # Extract text and metadata
            text = transcript.text.strip()
            duration = transcript.duration if hasattr(transcript, 'duration') else None
            detected_language = transcript.language if hasattr(transcript, 'language') else language

            # Clean up common Whisper API artifacts
            text = clean_transcription(text)

            # Log full transcription for debugging
            logger.info(f"✅ Transcription successful: '{text}' (duration: {duration}s, language: {detected_language})")

            # Return result with metadata
            return {
                "success": True,
                "text": text,
                "language": detected_language,
                "duration": duration
            }

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.info(f"🗑️ Cleaned up temp file: {temp_path}")

    except Exception as e:
        logger.error(f"❌ Error transcribing audio: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "text": ""
        }


def validate_audio_file(audio_file) -> Dict[str, Any]:
    """
    Validate audio file before transcription

    Args:
        audio_file: Audio file object

    Returns:
        dict: Validation result
    """
    # Check if file exists
    if not audio_file:
        return {
            "valid": False,
            "error": "No audio file provided"
        }

    # Check file size (max 25MB for Whisper API)
    MAX_SIZE = 25 * 1024 * 1024  # 25MB
    audio_file.seek(0, 2)  # Seek to end
    size = audio_file.tell()
    audio_file.seek(0)  # Reset to beginning

    if size > MAX_SIZE:
        return {
            "valid": False,
            "error": f"File too large ({size / 1024 / 1024:.1f}MB). Max size: 25MB"
        }

    if size == 0:
        return {
            "valid": False,
            "error": "Audio file is empty"
        }

    # Check file type (Whisper supports: mp3, mp4, mpeg, mpga, m4a, wav, webm)
    ALLOWED_EXTENSIONS = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm', 'ogg']
    filename = audio_file.filename.lower() if hasattr(audio_file, 'filename') else ''

    if filename:
        extension = filename.rsplit('.', 1)[-1] if '.' in filename else ''
        if extension not in ALLOWED_EXTENSIONS:
            return {
                "valid": False,
                "error": f"Unsupported file type: {extension}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }

    return {
        "valid": True,
        "size": size,
        "extension": extension if filename else 'unknown'
    }
