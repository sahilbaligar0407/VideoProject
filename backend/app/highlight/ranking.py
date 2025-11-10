"""
Clip ranking system for viral content.
Implements a 0-5 rating scale based on multiple factors.
"""

import numpy as np
from typing import List, Dict, Any
from app.models import HighlightSegment, ClipRanking
from app.settings import settings

class ClipRanker:
    """Ranks clips on a 0-5 scale based on virality potential"""
    
    def __init__(self):
        self.ranking_weights = settings.ranking_weights
        self.viral_thresholds = {
            "excellent": 4.5,    # 4.5-5.0: Exceptional viral potential
            "very_good": 4.0,    # 4.0-4.4: High viral potential
            "good": 3.5,         # 3.5-3.9: Good viral potential
            "average": 3.0,      # 3.0-3.4: Moderate viral potential
            "below_average": 2.0, # 2.0-2.9: Below average
            "poor": 1.0,         # 1.0-1.9: Poor viral potential
            "very_poor": 0.0     # 0.0-0.9: Very poor viral potential
        }
    
    def rank_clips(self, segments: List[HighlightSegment], 
                   transcription: Any = None, 
                   video_path: str = None) -> List[HighlightSegment]:
        """Rank clips using the comprehensive scoring system"""
        print(f"🏆 Starting clip ranking for {len(segments)} segments...")
        
        if not segments:
            return []
        
        # Calculate ranking for each segment and create updated instances
        ranked_segments = []
        for segment in segments:
            ranking = self._calculate_clip_ranking(segment, transcription, video_path)
            
            # Create updated segment with ranking using model_copy (Pydantic v2)
            updated_segment = segment.model_copy(update={
                'ranking': ranking,
                'confidence_score': ranking.viral_score / 5.0
            })
            
            ranked_segments.append(updated_segment)
        
        # Sort by viral score (highest first)
        ranked_segments.sort(key=lambda x: x.ranking.viral_score if x.ranking else 0.0, reverse=True)
        
        if ranked_segments and ranked_segments[0].ranking:
            print(f"🏆 Ranking complete! Top clip score: {ranked_segments[0].ranking.viral_score:.1f}/5.0")
        else:
            print(f"🏆 Ranking complete!")
        
        return ranked_segments
    
    def _calculate_clip_ranking(self, segment: HighlightSegment, 
                               transcription: Any = None, 
                               video_path: str = None) -> ClipRanking:
        """Calculate comprehensive ranking for a single clip"""
        
        # Initialize scoring factors
        factors = {}
        
        # 1. Viral Similarity Score (0-5 scale)
        viral_score = self._calculate_viral_similarity_score(segment)
        factors["viral_similarity"] = viral_score
        
        # 2. Content Engagement Score (0-5 scale)
        engagement_score = self._calculate_engagement_score(segment, transcription)
        factors["content_engagement"] = engagement_score
        
        # 3. Audio Analysis Score (0-5 scale)
        audio_score = self._calculate_audio_score(segment)
        factors["audio_analysis"] = audio_score
        
        # 4. Story Structure Score (0-5 scale)
        story_score = self._calculate_story_structure_score(segment, transcription)
        factors["story_structure"] = story_score
        
        # 5. AI Analysis Score (0-5 scale)
        ai_score = self._calculate_ai_analysis_score(segment)
        factors["ai_analysis"] = ai_score
        
        # 6. Duration Optimization Score (0-5 scale)
        duration_score = self._calculate_duration_score(segment)
        factors["duration_optimization"] = duration_score
        
        # 7. Position Score (0-5 scale)
        position_score = self._calculate_position_score(segment, transcription)
        factors["position"] = position_score
        
        # Calculate weighted final score
        final_score = self._calculate_weighted_score(factors)
        
        # Calculate sub-scores for detailed breakdown
        engagement_potential = self._calculate_engagement_potential(factors)
        shareability = self._calculate_shareability(factors)
        trending_potential = self._calculate_trending_potential(factors)
        
        return ClipRanking(
            viral_score=final_score,
            engagement_potential=engagement_potential,
            shareability=shareability,
            trending_potential=trending_potential,
            ranking_factors=factors
        )
    
    def _calculate_viral_similarity_score(self, segment: HighlightSegment) -> float:
        """Calculate viral similarity score (0-5)"""
        base_score = segment.confidence_score * 5.0
        
        # Boost for viral similarity detection method
        if segment.detection_method == "viral_similarity":
            base_score *= 1.2
        
        # Boost for viral keywords
        viral_keywords = ["viral", "trending", "controversial", "shocking", "exposed"]
        keyword_boost = 0
        for keyword in viral_keywords:
            if keyword in segment.keywords:
                keyword_boost += 0.3
        
        final_score = min(5.0, base_score + keyword_boost)
        return round(final_score, 1)
    
    def _calculate_engagement_score(self, segment: HighlightSegment, transcription: Any) -> float:
        """Calculate content engagement score (0-5)"""
        score = 2.5  # Base score
        
        # Boost for questions and interactive content
        if any(word in segment.keywords for word in ["question", "engagement"]):
            score += 1.0
        
        # Boost for emotional content
        emotional_keywords = ["amazing", "incredible", "wow", "unbelievable", "omg"]
        for keyword in emotional_keywords:
            if keyword in segment.keywords:
                score += 0.5
        
        # Boost for call-to-action content
        cta_keywords = ["subscribe", "follow", "like", "share", "comment"]
        for keyword in cta_keywords:
            if keyword in segment.keywords:
                score += 0.8
        
        # Boost for transcript quality
        if hasattr(transcription, 'segments') and transcription.segments:
            relevant_text = ""
            for seg in transcription.segments:
                if 'start' in seg and 'end' in seg:
                    if (seg['start'] >= segment.start_time and seg['end'] <= segment.end_time):
                        relevant_text += seg.get('text', '')
            
            if len(relevant_text.strip()) > 50:
                score += 0.5
            elif len(relevant_text.strip()) > 20:
                score += 0.3
        
        return min(5.0, round(score, 1))
    
    def _calculate_audio_score(self, segment: HighlightSegment) -> float:
        """Calculate audio analysis score (0-5)"""
        score = 2.5  # Base score
        
        # Boost for high-energy audio
        if any(word in segment.keywords for word in ["high_energy", "dynamic_audio"]):
            score += 1.0
        
        # Boost for rhythmic content
        if any(word in segment.keywords for word in ["rhythm", "beat", "music"]):
            score += 0.8
        
        # Boost for sudden changes/reactions
        if any(word in segment.keywords for word in ["sudden_change", "reaction", "surprise"]):
            score += 0.7
        
        # Boost for dramatic pauses
        if any(word in segment.keywords for word in ["dramatic_pause", "silence", "tension"]):
            score += 0.5
        
        return min(5.0, round(score, 1))
    
    def _calculate_story_structure_score(self, segment: HighlightSegment, transcription: Any) -> float:
        """Calculate story structure score (0-5)"""
        score = 2.5  # Base score
        
        # Boost for story structure elements
        if any(word in segment.keywords for word in ["opening", "hook", "introduction"]):
            score += 1.0
        
        if any(word in segment.keywords for word in ["climax", "middle", "peak"]):
            score += 1.2
        
        if any(word in segment.keywords for word in ["conclusion", "summary", "ending"]):
            score += 0.8
        
        return min(5.0, round(score, 1))
    
    def _calculate_ai_analysis_score(self, segment: HighlightSegment) -> float:
        """Calculate AI analysis score (0-5)"""
        score = 2.5  # Base score
        
        # Boost for AI-analyzed content
        if segment.detection_method == "chatgpt_analysis":
            score += 1.5
        
        # Boost for high-confidence AI detection
        if segment.confidence_score > 0.8:
            score += 0.5
        
        return min(5.0, round(score, 1))
    
    def _calculate_duration_score(self, segment: HighlightSegment) -> float:
        """Calculate duration optimization score (0-5)"""
        duration = segment.duration
        
        # Optimal duration for short-form content
        if 15 <= duration <= 60:
            return 5.0
        elif 10 <= duration < 15 or 60 < duration <= 90:
            return 4.0
        elif 5 <= duration < 10 or 90 < duration <= 120:
            return 3.0
        elif 2 <= duration < 5 or duration > 120:
            return 2.0
        else:
            return 1.0
    
    def _calculate_position_score(self, segment: HighlightSegment, transcription: Any) -> float:
        """Calculate position score (0-5)"""
        if not hasattr(transcription, 'duration') or transcription.duration <= 0:
            return 3.0
        
        video_duration = transcription.duration
        segment_center = (segment.start_time + segment.end_time) / 2
        position_ratio = segment_center / video_duration
        
        # Beginning and end are better for retention
        if position_ratio < 0.2:  # First 20%
            return 5.0
        elif position_ratio > 0.8:  # Last 20%
            return 4.5
        elif 0.3 < position_ratio < 0.7:  # Middle (good for climax)
            return 4.0
        else:
            return 3.0
    
    def _calculate_weighted_score(self, factors: Dict[str, float]) -> float:
        """Calculate weighted final score (0-5)"""
        total_score = 0.0
        total_weight = 0.0
        
        for factor_name, score in factors.items():
            weight = self.ranking_weights.get(factor_name, 0.1)
            total_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 2.5  # Default middle score
        
        return round(final_score, 1)
    
    def _calculate_engagement_potential(self, factors: Dict[str, float]) -> float:
        """Calculate engagement potential (0-1)"""
        engagement_factors = ["content_engagement", "viral_similarity", "ai_analysis"]
        scores = [factors.get(factor, 0) for factor in engagement_factors]
        
        if scores:
            return min(1.0, np.mean(scores) / 5.0)
        return 0.5
    
    def _calculate_shareability(self, factors: Dict[str, float]) -> float:
        """Calculate shareability potential (0-1)"""
        shareability_factors = ["viral_similarity", "content_engagement", "story_structure"]
        scores = [factors.get(factor, 0) for factor in shareability_factors]
        
        if scores:
            return min(1.0, np.mean(scores) / 5.0)
        return 0.5
    
    def _calculate_trending_potential(self, factors: Dict[str, float]) -> float:
        """Calculate trending potential (0-1)"""
        trending_factors = ["viral_similarity", "ai_analysis", "audio_analysis"]
        scores = [factors.get(factor, 0) for factor in trending_factors]
        
        if scores:
            return min(1.0, np.mean(scores) / 5.0)
        return 0.5
    
    def get_ranking_summary(self, segments: List[HighlightSegment]) -> Dict[str, Any]:
        """Get summary statistics for ranked clips"""
        if not segments:
            return {}
        
        scores = [seg.ranking.viral_score for seg in segments if seg.ranking]
        
        if not scores:
            return {}
        
        summary = {
            "total_clips": len(segments),
            "average_score": round(np.mean(scores), 2),
            "top_score": round(max(scores), 1),
            "lowest_score": round(min(scores), 1),
            "score_distribution": {
                "excellent": len([s for s in scores if s >= 4.5]),
                "very_good": len([s for s in scores if 4.0 <= s < 4.5]),
                "good": len([s for s in scores if 3.5 <= s < 4.0]),
                "average": len([s for s in scores if 3.0 <= s < 3.5]),
                "below_average": len([s for s in scores if 2.0 <= s < 3.0]),
                "poor": len([s for s in scores if 1.0 <= s < 2.0]),
                "very_poor": len([s for s in scores if s < 1.0])
            }
        }
        
        return summary
    
    def print_ranking_report(self, segments: List[HighlightSegment]):
        """Print a detailed ranking report"""
        print(f"\n🏆 CLIP RANKING REPORT")
        print(f"=" * 50)
        
        for i, segment in enumerate(segments[:10], 1):  # Top 10
            ranking = segment.ranking
            if ranking:
                print(f"{i:2d}. Score: {ranking.viral_score:4.1f}/5.0 | "
                      f"Duration: {segment.duration:5.1f}s | "
                      f"Method: {segment.detection_method or 'unknown'}")
                print(f"    Engagement: {ranking.engagement_potential:.2f} | "
                      f"Shareability: {ranking.shareability:.2f} | "
                      f"Trending: {ranking.trending_potential:.2f}")
                print(f"    Time: {segment.start_time:6.1f}s - {segment.end_time:6.1f}s")
                print()
        
        # Print summary
        summary = self.get_ranking_summary(segments)
        if summary:
            print(f"📊 RANKING SUMMARY")
            print(f"-" * 30)
            print(f"Total clips: {summary['total_clips']}")
            print(f"Average score: {summary['average_score']}/5.0")
            print(f"Top score: {summary['top_score']}/5.0")
            print(f"Score distribution:")
            for category, count in summary['score_distribution'].items():
                if count > 0:
                    print(f"  {category.replace('_', ' ').title()}: {count}")

