"""
AI text generation for ClipGenius Pipeline v2.
Generates titles, hooks, and CTAs using OpenAI Chat API.
"""

import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.settings import settings

def generate_titles_cta(transcript_text: str, viral_terms: List[str] = None, 
                       topics: List[str] = None, model: str = "gpt-4o") -> Dict[str, Any]:
    """
    Generate titles, hooks, and CTAs using OpenAI Chat API
    
    Args:
        transcript_text: Transcript text to analyze
        viral_terms: List of viral terms for context
        topics: List of topics for context
        model: OpenAI model to use
        
    Returns:
        Dict with generated content
    """
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured")
    
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Prepare context
    context_parts = [f"Transcript: {transcript_text[:1000]}..."]  # Limit transcript length
    
    if viral_terms:
        context_parts.append(f"Viral terms: {', '.join(viral_terms[:10])}")
    
    if topics:
        context_parts.append(f"Topics: {', '.join(topics)}")
    
    context = "\n\n".join(context_parts)
    
    # Define the schema for structured output
    schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Engaging title for the clip (max 60 characters)"
            },
            "hook": {
                "type": "string", 
                "description": "Attention-grabbing hook line (max 8 words)"
            },
            "cta": {
                "type": "string",
                "enum": ["SUBSCRIBE", "WATCH_PART_2", "FOLLOW", "COMMENT", "LIKE", "SHARE"],
                "description": "Call-to-action for the clip"
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5 relevant keywords for SEO"
            },
            "viral_potential": {
                "type": "number",
                "minimum": 0,
                "maximum": 10,
                "description": "Viral potential score (0-10)"
            }
        },
        "required": ["title", "hook", "cta", "keywords", "viral_potential"]
    }
    
    # Create the prompt
    system_prompt = """You are a viral content expert. Analyze the transcript and generate engaging titles, hooks, and CTAs that will maximize engagement on social media platforms like TikTok, Instagram Reels, and YouTube Shorts.

Focus on:
- Creating hooks that grab attention in the first 3 seconds
- Using trending language and patterns
- Making titles that are clickable and shareable
- Choosing CTAs that drive specific actions
- Identifying viral potential based on content analysis

Return exactly 3 variants, each optimized for different audience types."""
    
    user_prompt = f"""Based on this content:

{context}

Generate 3 engaging variants for social media. Each should be optimized for maximum viral potential.

Focus on creating content that:
1. Hooks viewers immediately
2. Uses trending language and patterns  
3. Drives specific engagement actions
4. Is optimized for short-form video platforms

Return the results in the specified JSON schema with exactly 3 variants."""

    try:
        print(f"🤖 Generating AI titles/CTAs with {model}")
        
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse the response
        content = response.choices[0].message.content
        result = json.loads(content)
        
        print(f"✅ AI text generation complete")
        return result
        
    except Exception as e:
        print(f"❌ AI text generation failed: {e}")
        # Return fallback content
        return _generate_fallback_content(transcript_text)

def generate_hook_lines(transcript_text: str, count: int = 5) -> List[str]:
    """
    Generate multiple hook lines for A/B testing
    
    Args:
        transcript_text: Transcript text to analyze
        count: Number of hook lines to generate
        
    Returns:
        List of hook lines
    """
    if not settings.openai_api_key:
        return _generate_fallback_hooks(transcript_text, count)
    
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Create the prompt
    system_prompt = """You are a hook line specialist. Generate attention-grabbing opening lines that will make viewers stop scrolling and watch the full video.

Focus on:
- Questions that create curiosity
- Bold statements that challenge assumptions
- Numbers and specific details
- Emotional triggers
- Trending patterns and language

Each hook should be 5-8 words maximum and designed to grab attention in the first 3 seconds."""
    
    user_prompt = f"""Based on this transcript:

{transcript_text[:500]}...

Generate {count} different hook lines, each optimized for maximum engagement on social media.

Each hook should be:
- 5-8 words maximum
- Designed to grab attention immediately
- Different from the others (no repetition)
- Optimized for the specific content

Return as a simple list of hook lines."""

    try:
        print(f"🤖 Generating {count} hook lines")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # Parse the response (could be various formats)
        if "1." in content or "-" in content:
            # Extract numbered or bulleted lines
            lines = []
            for line in content.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering/bullets and clean up
                    clean_line = line.split('.', 1)[-1].strip().lstrip('- ').strip()
                    if clean_line:
                        lines.append(clean_line)
            return lines[:count]
        else:
            # Split by newlines and clean up
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            return lines[:count]
        
    except Exception as e:
        print(f"❌ Hook line generation failed: {e}")
        return _generate_fallback_hooks(transcript_text, count)

def _generate_fallback_content(transcript_text: str) -> Dict[str, Any]:
    """Generate fallback content when AI generation fails"""
    # Extract key phrases from transcript
    words = transcript_text.split()[:20]  # First 20 words
    key_phrase = " ".join(words[:5])
    
    return {
        "title": f"{key_phrase[:50]}...",
        "hook": f"Watch this {words[0] if words else 'amazing'} moment!",
        "cta": "SUBSCRIBE",
        "keywords": words[:5] if words else ["content", "video", "interesting"],
        "viral_potential": 5
    }

def _generate_fallback_hooks(transcript_text: str, count: int) -> List[str]:
    """Generate fallback hook lines when AI generation fails"""
    words = transcript_text.split()
    
    hooks = [
        "You won't believe what happened next!",
        "This is absolutely incredible!",
        "Watch this amazing moment!",
        "You need to see this!",
        "This will blow your mind!"
    ]
    
    # Customize based on content
    if words:
        first_word = words[0].lower()
        if first_word in ["i", "we", "they"]:
            hooks.append(f"{first_word.title()} just revealed something shocking!")
        elif first_word in ["the", "this", "that"]:
            hooks.append(f"{first_word.title()} is absolutely incredible!")
    
    return hooks[:count]

def analyze_viral_potential(transcript_text: str, engagement_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze viral potential of content
    
    Args:
        transcript_text: Transcript text to analyze
        engagement_metrics: Optional engagement metrics
        
    Returns:
        Dict with viral potential analysis
    """
    # Simple heuristic analysis
    text_lower = transcript_text.lower()
    
    # Viral indicators
    viral_indicators = {
        "questions": text_lower.count("?") > 0,
        "exclamations": text_lower.count("!") > 0,
        "numbers": any(char.isdigit() for char in transcript_text),
        "emotional_words": any(word in text_lower for word in ["amazing", "incredible", "shocking", "unbelievable"]),
        "trending_topics": any(word in text_lower for word in ["viral", "trending", "popular", "hot"]),
        "call_to_action": any(word in text_lower for word in ["watch", "see", "check", "follow", "subscribe"])
    }
    
    # Calculate score
    score = sum(viral_indicators.values()) / len(viral_indicators) * 10
    
    return {
        "viral_score": round(score, 1),
        "indicators": viral_indicators,
        "recommendations": _get_viral_recommendations(viral_indicators, score)
    }

def _get_viral_recommendations(indicators: Dict[str, bool], score: float) -> List[str]:
    """Get recommendations to improve viral potential"""
    recommendations = []
    
    if not indicators["questions"]:
        recommendations.append("Add questions to create curiosity")
    
    if not indicators["emotional_words"]:
        recommendations.append("Use more emotional and impactful language")
    
    if not indicators["call_to_action"]:
        recommendations.append("Include clear calls-to-action")
    
    if score < 5:
        recommendations.append("Consider adding trending hashtags or topics")
        recommendations.append("Make the opening more attention-grabbing")
    
    return recommendations
