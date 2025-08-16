"""
Multi-language caption translation for ClipGenius Pipeline v2.
Uses OpenAI API for high-quality translation with timestamp preservation.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.settings import settings
import json
import os

def translate_captions(
    captions: List[Dict[str, Any]],
    target_language: str = "en",
    source_language: str = "auto"
) -> List[Dict[str, Any]]:
    """
    Translate captions to target language using OpenAI API.
    
    Args:
        captions: List of caption dictionaries with start, end, text
        target_language: Target language code (e.g., "es", "fr", "hi")
        source_language: Source language code or "auto" for detection
        
    Returns:
        List of translated captions with preserved timestamps
    """
    if not captions:
        return []
    
    # Initialize OpenAI client
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Prepare translation prompt
    system_prompt = f"""You are a professional caption translator. Translate the following captions to {target_language}.

IMPORTANT RULES:
1. Preserve ALL timestamps exactly as they appear
2. Maintain the same number of captions
3. Keep the same start/end times
4. Translate only the text content
5. Maintain natural flow and readability
6. Use appropriate cultural context for {target_language}

Format: Return ONLY a JSON array of objects with start, end, and text fields.
Example: [{{"start": 0.0, "end": 2.0, "text": "translated text"}}]"""

    # Prepare captions for translation
    caption_texts = []
    for caption in captions:
        caption_texts.append({
            "start": caption.get("start", 0),
            "end": caption.get("end", 0),
            "text": caption.get("text", "")
        })
    
    try:
        # Send translation request
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use faster model for translation
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate these captions to {target_language}:\n\n{json.dumps(caption_texts, indent=2)}"}
            ],
            temperature=0.3,  # Lower temperature for consistent translation
            max_tokens=2000
        )
        
        # Parse response
        translated_content = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        if "```json" in translated_content:
            # Extract JSON from code block
            start_idx = translated_content.find("```json") + 7
            end_idx = translated_content.rfind("```")
            json_str = translated_content[start_idx:end_idx].strip()
        else:
            # Try to find JSON array in response
            start_idx = translated_content.find("[")
            end_idx = translated_content.rfind("]") + 1
            if start_idx != -1 and end_idx != -1:
                json_str = translated_content[start_idx:end_idx]
            else:
                json_str = translated_content
        
        # Parse translated captions
        translated_captions = json.loads(json_str)
        
        # Validate structure
        if not isinstance(translated_captions, list):
            raise ValueError("Translation response is not a list")
        
        # Ensure all required fields are present
        for caption in translated_captions:
            if not all(key in caption for key in ["start", "end", "text"]):
                raise ValueError("Translated caption missing required fields")
        
        print(f"✅ Successfully translated {len(translated_captions)} captions to {target_language}")
        return translated_captions
        
    except Exception as e:
        print(f"❌ Translation failed: {e}")
        # Return original captions on failure
        return captions

def detect_caption_language(captions: List[Dict[str, Any]]) -> str:
    """
    Detect the language of captions using OpenAI API.
    
    Args:
        captions: List of caption dictionaries
        
    Returns:
        Detected language code (e.g., "en", "es", "fr")
    """
    if not captions:
        return "en"  # Default to English
    
    # Initialize OpenAI client
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Sample text from captions (first few captions)
    sample_texts = []
    for caption in captions[:3]:  # Use first 3 captions
        text = caption.get("text", "").strip()
        if text and len(text) > 10:  # Only use substantial text
            sample_texts.append(text)
    
    if not sample_texts:
        return "en"
    
    # Combine sample texts
    combined_text = " ".join(sample_texts)
    
    try:
        # Send language detection request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a language detection expert. Detect the language of the given text and return ONLY the ISO 639-1 language code (e.g., 'en', 'es', 'fr', 'de', 'hi', 'ja', 'ko', 'zh')."},
                {"role": "user", "content": f"Detect the language of this text:\n\n{combined_text}"}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        detected_lang = response.choices[0].message.content.strip().lower()
        
        # Validate language code
        valid_langs = ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "hi", "ar", "nl", "sv", "da", "no", "fi", "pl", "tr", "he", "th", "vi", "id", "ms", "tl"]
        
        if detected_lang in valid_langs:
            print(f"✅ Detected language: {detected_lang}")
            return detected_lang
        else:
            print(f"⚠️ Invalid language code detected: {detected_lang}, defaulting to 'en'")
            return "en"
            
    except Exception as e:
        print(f"❌ Language detection failed: {e}, defaulting to 'en'")
        return "en"

def get_supported_languages() -> List[Dict[str, str]]:
    """Get list of supported languages for translation"""
    return [
        {"code": "en", "name": "English", "native": "English"},
        {"code": "es", "name": "Spanish", "native": "Español"},
        {"code": "fr", "name": "French", "native": "Français"},
        {"code": "de", "name": "German", "native": "Deutsch"},
        {"code": "it", "name": "Italian", "native": "Italiano"},
        {"code": "pt", "name": "Portuguese", "native": "Português"},
        {"code": "ru", "name": "Russian", "native": "Русский"},
        {"code": "ja", "name": "Japanese", "native": "日本語"},
        {"code": "ko", "name": "Korean", "native": "한국어"},
        {"code": "zh", "name": "Chinese", "native": "中文"},
        {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
        {"code": "ar", "name": "Arabic", "native": "العربية"},
        {"code": "nl", "name": "Dutch", "native": "Nederlands"},
        {"code": "sv", "name": "Swedish", "native": "Svenska"},
        {"code": "da", "name": "Danish", "native": "Dansk"},
        {"code": "no", "name": "Norwegian", "native": "Norsk"},
        {"code": "fi", "name": "Finnish", "native": "Suomi"},
        {"code": "pl", "name": "Polish", "native": "Polski"},
        {"code": "tr", "name": "Turkish", "native": "Türkçe"},
        {"code": "he", "name": "Hebrew", "native": "עברית"},
        {"code": "th", "name": "Thai", "native": "ไทย"},
        {"code": "vi", "name": "Vietnamese", "native": "Tiếng Việt"},
        {"code": "id", "name": "Indonesian", "native": "Bahasa Indonesia"},
        {"code": "ms", "name": "Malay", "native": "Bahasa Melayu"},
        {"code": "tl", "name": "Tagalog", "native": "Tagalog"}
    ]

def batch_translate_captions(
    captions: List[Dict[str, Any]],
    target_languages: List[str],
    source_language: str = "auto"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Translate captions to multiple languages in batch.
    
    Args:
        captions: List of caption dictionaries
        target_languages: List of target language codes
        source_language: Source language code or "auto"
        
    Returns:
        Dictionary mapping language codes to translated captions
    """
    results = {}
    
    # Detect source language if auto
    if source_language == "auto":
        detected_lang = detect_caption_language(captions)
        source_language = detected_lang
        print(f"🔍 Auto-detected source language: {detected_lang}")
    
    # Add source language to results
    results[source_language] = captions
    
    # Translate to each target language
    for target_lang in target_languages:
        if target_lang == source_language:
            # Skip if target is same as source
            continue
            
        print(f"🌐 Translating to {target_lang}...")
        translated = translate_captions(captions, target_lang, source_language)
        results[target_lang] = translated
    
    return results

def validate_translation_quality(
    original_captions: List[Dict[str, Any]],
    translated_captions: List[Dict[str, Any]],
    target_language: str
) -> Dict[str, Any]:
    """
    Validate translation quality and provide feedback.
    
    Args:
        original_captions: Original captions
        translated_captions: Translated captions
        target_language: Target language
        
    Returns:
        Validation results and quality metrics
    """
    if len(original_captions) != len(translated_captions):
        return {
            "valid": False,
            "error": "Caption count mismatch",
            "original_count": len(original_captions),
            "translated_count": len(translated_captions)
        }
    
    # Check timestamp preservation
    timestamp_errors = []
    for i, (orig, trans) in enumerate(zip(original_captions, translated_captions)):
        if abs(orig.get("start", 0) - trans.get("start", 0)) > 0.01:
            timestamp_errors.append(f"Caption {i+1}: start time mismatch")
        if abs(orig.get("end", 0) - trans.get("end", 0)) > 0.01:
            timestamp_errors.append(f"Caption {i+1}: end time mismatch")
    
    # Check text length ratios (translation can vary in length)
    length_ratios = []
    for orig, trans in zip(original_captions, translated_captions):
        orig_len = len(orig.get("text", ""))
        trans_len = len(trans.get("text", ""))
        if orig_len > 0:
            ratio = trans_len / orig_len
            length_ratios.append(ratio)
    
    avg_length_ratio = sum(length_ratios) / len(length_ratios) if length_ratios else 1.0
    
    # Quality assessment
    quality_score = 100
    
    if timestamp_errors:
        quality_score -= 30
    
    if avg_length_ratio < 0.5 or avg_length_ratio > 2.0:
        quality_score -= 20
    
    if quality_score < 50:
        quality_level = "poor"
    elif quality_score < 75:
        quality_level = "fair"
    elif quality_score < 90:
        quality_level = "good"
    else:
        quality_level = "excellent"
    
    return {
        "valid": len(timestamp_errors) == 0,
        "quality_score": quality_score,
        "quality_level": quality_level,
        "timestamp_errors": timestamp_errors,
        "avg_length_ratio": avg_length_ratio,
        "caption_count": len(original_captions),
        "target_language": target_language
    }
