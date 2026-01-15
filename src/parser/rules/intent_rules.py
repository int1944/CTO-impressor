"""Intent detection rules for flight, hotel, and train intents."""

import re
from typing import Optional, Dict
from .pattern_matcher import PatternMatcher


class IntentRules:
    """Rules for detecting user intent (flight, hotel, train)."""
    
    # Intent patterns with confidence scores
    INTENT_PATTERNS: Dict[str, list[tuple[str, float]]] = {
        'flight': [
            (r'\b(book|want|need|looking for|search for)\s+(a\s+)?(flight|fly|airplane|airline|ticket)', 0.95),
            (r'\b(flight|fly|flying|airline)\s+(from|to|on|for|between)', 0.90),
            (r'\b(departure|destination|airport|depart|arrive)', 0.85),
            (r'\b(airline|aircraft|boarding)', 0.80),
        ],
        'hotel': [
            (r'\b(book|want|need|looking for|search for)\s+(a\s+)?(hotel|stay|accommodation|room|reservation)', 0.95),
            (r'\b(hotel|stay|accommodation|room|booking)\s+(in|at|for|from|near)', 0.90),
            (r'\b(check.?in|check.?out|checkin|checkout)', 0.85),
            (r'\b(lodging|resort|guesthouse)', 0.80),
        ],
        'train': [
            (r'\b(book|want|need|search for)\s+(a\s+)?(train|railway|rail|ticket)', 0.95),
            (r'\b(train|railway|rail)\s+(from|to|on|for|between)', 0.90),
            (r'\b(station|journey|platform|compartment)', 0.85),
            (r'\b(railway|locomotive)', 0.80),
        ]
    }
    
    def __init__(self):
        """Initialize intent rules."""
        self.pattern_matcher = PatternMatcher()
    
    def match(self, query: str) -> Optional[Dict[str, any]]:
        """
        Match query against intent patterns.
        
        Args:
            query: User query text
            
        Returns:
            Dict with 'intent' and 'confidence' if match found, None otherwise
        """
        if not query:
            return None
        
        best_match = None
        best_confidence = 0.0
        
        # Check each intent
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern, base_confidence in patterns:
                match = self.pattern_matcher.match_pattern(query, pattern, case_sensitive=False)
                if match:
                    # Use the base confidence from pattern
                    if base_confidence > best_confidence:
                        best_confidence = base_confidence
                        best_match = {
                            'intent': intent,
                            'confidence': base_confidence,
                            'match_text': match.group(0)
                        }
        
        # Only return if confidence is above threshold
        if best_match and best_confidence >= 0.75:
            return best_match
        
        return None
    
    def get_all_intents(self) -> list[str]:
        """Get list of all supported intents."""
        return list(self.INTENT_PATTERNS.keys())
