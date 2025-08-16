"""
Viral terms management for the Viral Similarity Engine.
"""

import json
import os
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from ..settings import settings


class ViralTerm(BaseModel):
    """Model for viral terms with weights."""
    term: str = Field(..., description="Viral term or phrase")
    weight: float = Field(default=1.0, ge=0.1, le=5.0, description="Weight for the term")


class ViralTermsManager:
    """Manages viral terms storage and retrieval."""
    
    def __init__(self, terms_file: str = "app/viral/viral_terms.json"):
        self.terms_file = terms_file
        self._ensure_terms_file()
    
    def _ensure_terms_file(self):
        """Ensure the terms file exists with default terms."""
        os.makedirs(os.path.dirname(self.terms_file), exist_ok=True)
        
        if not os.path.exists(self.terms_file):
            default_terms = [
                {"term": "wow", "weight": 1.2},
                {"term": "insane", "weight": 1.2},
                {"term": "no way", "weight": 1.3},
                {"term": "unbelievable", "weight": 1.1},
                {"term": "watch till the end", "weight": 1.4},
                {"term": "plot twist", "weight": 1.3},
                {"term": "clutch", "weight": 1.2},
                {"term": "this changes everything", "weight": 1.2},
                {"term": "mind-blowing", "weight": 1.1},
                {"term": "epic", "weight": 1.0},
                {"term": "perfect timing", "weight": 1.1},
                {"term": "fails", "weight": 1.0},
                {"term": "exposed", "weight": 1.1},
                {"term": "truth", "weight": 1.0},
                {"term": "drama", "weight": 1.0},
                {"term": "game changer", "weight": 1.2},
                {"term": "before and after", "weight": 1.2}
            ]
            self._save_terms([ViralTerm(**term) for term in default_terms])
    
    def _load_terms(self) -> List[ViralTerm]:
        """Load terms from JSON file."""
        try:
            with open(self.terms_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ViralTerm(**term) for term in data]
        except Exception as e:
            print(f"⚠️ Error loading viral terms: {e}")
            return []
    
    def _save_terms(self, terms: List[ViralTerm]):
        """Save terms to JSON file."""
        try:
            with open(self.terms_file, 'w', encoding='utf-8') as f:
                json.dump([term.dict() for term in terms], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving viral terms: {e}")
    
    def get_terms(self) -> List[ViralTerm]:
        """Get all viral terms."""
        return self._load_terms()
    
    def add_term(self, term: str, weight: float = 1.0) -> bool:
        """Add a new viral term."""
        terms = self._load_terms()
        
        # Check if term already exists
        if any(t.term.lower() == term.lower() for t in terms):
            return False
        
        # Check max terms limit
        if len(terms) >= settings.viral_max_terms:
            return False
        
        new_term = ViralTerm(term=term, weight=weight)
        terms.append(new_term)
        self._save_terms(terms)
        return True
    
    def update_term(self, term: str, weight: float) -> bool:
        """Update weight of existing term."""
        terms = self._load_terms()
        
        for t in terms:
            if t.term.lower() == term.lower():
                t.weight = weight
                self._save_terms(terms)
                return True
        
        return False
    
    def remove_term(self, term: str) -> bool:
        """Remove a viral term."""
        terms = self._load_terms()
        original_count = len(terms)
        
        terms = [t for t in terms if t.term.lower() != term.lower()]
        
        if len(terms) < original_count:
            self._save_terms(terms)
            return True
        
        return False
    
    def get_terms_dict(self) -> Dict[str, float]:
        """Get terms as a dictionary for easy lookup."""
        terms = self._load_terms()
        return {term.term: term.weight for term in terms}


# Global instance
_viral_terms_manager = ViralTermsManager()


def get_viral_terms() -> List[ViralTerm]:
    """Get all viral terms."""
    return _viral_terms_manager.get_terms()


def add_viral_term(term: str, weight: float = 1.0) -> bool:
    """Add a new viral term."""
    return _viral_terms_manager.add_term(term, weight)


def update_viral_term(term: str, weight: float) -> bool:
    """Update weight of existing term."""
    return _viral_terms_manager.update_term(term, weight)


def remove_viral_term(term: str) -> bool:
    """Remove a viral term."""
    return _viral_terms_manager.remove_term(term)


def get_viral_terms_dict() -> Dict[str, float]:
    """Get terms as a dictionary for easy lookup."""
    return _viral_terms_manager.get_terms_dict()
