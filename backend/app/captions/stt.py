"""
Speech-to-Text module for ClipGenius Pipeline v2.
Enhanced Whisper integration with language detection and translation.
"""

import os
import tempfile
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.settings import settings

def transcribe_audio(audio_path: str, language: str = "auto", 
                    translate_to: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_path: Path to audio file
        language: Language code or "auto" for detection
        translate_to: Target language for translation (optional)
        
    Returns:
        Transcription result with segments and metadata
    """
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured")
    
    client = OpenAI(api_key=settings.openai_api_key)
    
    try:
        # Prepare transcription parameters
        transcription_params = {
            "file": open(audio_path, "rb"),
            "model": settings.whisper_model,
            "response_format": "verbose_json",
            "temperature": 0
        }
        
        # Set language if specified
        if language != "auto":
            transcription_params["language"] = language
        
        # Enable translation if requested
        if translate_to:
            transcription_params["translate"] = True
        
        print(f"🎤 Transcribing audio: {audio_path}")
        print(f"   Language: {language}, Translate: {translate_to or 'No'}")
        
        # Perform transcription
        response = client.audio.transcriptions.create(**transcription_params)
        
        # Extract language information
        detected_language = response.language if hasattr(response, 'language') else language
        
        # Process segments
        segments = []
        if hasattr(response, 'segments') and response.segments:
            for segment in response.segments:
                segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "avg_logprob": getattr(segment, 'avg_logprob', 0.0),
                    "compression_ratio": getattr(segment, 'compression_ratio', 0.0),
                    "no_speech_prob": getattr(segment, 'no_speech_prob', 0.0)
                })
        
        result = {
            "text": response.text,
            "language": detected_language,
            "segments": segments,
            "duration": getattr(response, 'duration', 0.0),
            "translated": bool(translate_to)
        }
        
        print(f"✅ Transcription complete: {len(segments)} segments, language: {detected_language}")
        return result
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        raise
    
    finally:
        # Close file
        if 'file' in locals():
            transcription_params['file'].close()

def detect_language(audio_path: str) -> str:
    """
    Detect language of audio content
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Detected language code
    """
    try:
        # Use a short transcription to detect language
        result = transcribe_audio(audio_path, language="auto")
        return result.get("language", "en")
    except Exception as e:
        print(f"⚠️ Language detection failed: {e}")
        return "en"  # Default to English

def transcribe_audio_chunked(audio_path: str, chunk_duration: int = 30, 
                            language: str = "auto", translate_to: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe long audio files in chunks to avoid timeouts
    
    Args:
        audio_path: Path to audio file
        chunk_duration: Duration of each chunk in seconds
        language: Language code or "auto"
        translate_to: Target language for translation (optional)
        
    Returns:
        Combined transcription result
    """
    # This would require audio splitting logic
    # For now, fall back to regular transcription
    return transcribe_audio(audio_path, language, translate_to)

def get_supported_languages() -> List[Dict[str, str]]:
    """Get list of supported languages for transcription"""
    return [
        {"code": "en", "name": "English"},
        {"code": "es", "name": "Spanish"},
        {"code": "fr", "name": "French"},
        {"code": "de", "name": "German"},
        {"code": "it", "name": "Italian"},
        {"code": "pt", "name": "Portuguese"},
        {"code": "ru", "name": "Russian"},
        {"code": "ja", "name": "Japanese"},
        {"code": "ko", "name": "Korean"},
        {"code": "zh", "name": "Chinese"},
        {"code": "hi", "name": "Hindi"},
        {"code": "ar", "name": "Arabic"},
        {"code": "auto", "name": "Auto-detect"}
    ]

def validate_language_code(language: str) -> bool:
    """Validate if a language code is supported"""
    supported_codes = [lang["code"] for lang in get_supported_languages()]
    return language in supported_codes

def extract_audio_segments(transcription: Dict[str, Any], 
                          start_time: float, end_time: float) -> List[Dict[str, Any]]:
    """
    Extract transcription segments within a time range
    
    Args:
        transcription: Transcription result
        start_time: Start time in seconds
        end_time: End time in seconds
        
    Returns:
        List of segments within the time range
    """
    segments = transcription.get("segments", [])
    
    # Filter segments within time range
    range_segments = []
    for segment in segments:
        seg_start = segment.get("start", 0)
        seg_end = segment.get("end", 0)
        
        # Check for overlap
        if seg_end > start_time and seg_start < end_time:
            # Adjust segment timing to clip boundaries
            adjusted_start = max(0, seg_start - start_time)
            adjusted_end = min(end_time - start_time, seg_end - start_time)
            
            range_segments.append({
                "start": adjusted_start,
                "end": adjusted_end,
                "text": segment.get("text", ""),
                "avg_logprob": segment.get("avg_logprob", 0.0)
            })
    
    return range_segments

def merge_transcription_segments(segments: List[Dict[str, Any]]) -> str:
    """
    Merge transcription segments into continuous text
    
    Args:
        segments: List of transcription segments
        
    Returns:
        Merged text
    """
    if not segments:
        return ""
    
    # Sort by start time
    sorted_segments = sorted(segments, key=lambda x: x["start"])
    
    # Merge text with proper spacing
    merged_text = ""
    for i, segment in enumerate(sorted_segments):
        text = segment.get("text", "").strip()
        
        if i > 0:
            # Add space between segments
            merged_text += " "
        
        merged_text += text
    
    return merged_text
