"""Intent detection rules for flight, hotel, and train intents."""

import re
import os
import json
from typing import Optional, Dict
from pathlib import Path
from .pattern_matcher import PatternMatcher


class IntentRules:
    """Rules for detecting user intent (flight, hotel, train)."""
    
    # Intent patterns with confidence scores
    INTENT_PATTERNS: Dict[str, list[tuple[str, float]]] = {
        'flight': [
            (r'\b(book|want|need|looking for|search for)\s+(a\s+)?(flight|fly|airplane|airline|ticket)', 0.95),
            (r'\b(flight|fly|flying|airline)\s+(from|to|on|for|between)', 0.90),
            # Match "flight" when it appears after cities/keywords (e.g., "Mumbai to Delhi flight")
            (r'\b(from|to|between)\s+[^.]+\s+(flight|fly|flying)\b', 0.88),
            (r'\b\w+\s+(to|from)\s+\w+\s+(flight|fly|flying)\b', 0.88),
            # Match standalone "flight" word (lower confidence to avoid false positives)
            (r'\b(flight|fly|flying)\b', 0.78),
            (r'\b(departure|destination|airport|depart|arrive)', 0.85),
            (r'\b(airline|aircraft|boarding)', 0.80),
            (r'\b(show me|find|list)\s+(the\s+)?flights?\b', 0.90),
            (r'\b(want to|need to|going to)\s+fly\b', 0.90),
            (r'\b(round\s*trip|round-trip|return\s+flight|returning|coming back)\b', 0.90),
            (r'\b(multi[-\s]?city|two[-\s]?city|three[-\s]?city)\b', 0.85),
            (r'\b(non[-\s]?stop|direct\s+flight)\b', 0.85),
            (r'\b(cheapest|lowest\s+fare|budget\s+flight|cheap\s+flight)\b', 0.82),
            (r'\b(flight)\s+(under|within)\s+(₹|rs\.?|inr|usd|eur|\$)?\s*\d+[,\d]*\b', 0.80),
            (r'\b(confirm|reserve|book\s+this|go\s+ahead)\s+(flight|ticket)\b', 0.80),
            (r'\b(cancel|refund|change\s+date|reschedule)\s+(flight|ticket)\b', 0.80),
            (r'\b(payment|pay\s+with|upi|card|cards|split\s+payment)\b', 0.78),
            (r'\b(travel|trip|vacation)\s+(from|to|for|between)\b', 0.80),
            (r'\b(where can i fly|suggest a destination|surprise me)\b', 0.80),
            (r'\b(cheaper|discounts|deals|lowest fare|cheapest day to fly)\b', 0.78),
            (r'\b(payment methods|international cards|split the payment)\b', 0.78),
            (r'\b(cancellation fee|refundable|change the date)\b', 0.78),
            (r'\b(layover|terminal|flight duration|how long is the flight|food included)\b', 0.78),
            (r'\b(wheelchair assistance|traveling with a pet|unaccompanied minor|special meal)\b', 0.78),
            (r'\b(cancel everything|fastest option|get me there)\b', 0.78),
            (r'\b(sometime next month|around christmas|first half of \w+|next week)\b', 0.76),
            (r'\b(this is taking too long|i don\'?t care|just get me there)\b', 0.76),
            (r'\b(passenger|passengers)\b', 0.76),
        ],
        'hotel': [
            (r'\b(book|want|need|looking for|search for)\s+(a\s+)?(hotel|stay|accommodation|room|reservation)', 0.95),
            (r'\b(hotel|stay|accommodation|room|booking)\s+(in|at|for|from|near)', 0.90),
            # Match "hotel" when it appears after cities/keywords (e.g., "Mumbai hotel")
            (r'\b\w+\s+(hotel|stay|accommodation|room)\b', 0.88),
            (r'\b(in|at|for)\s+[^.]+\s+(hotel|stay|accommodation)\b', 0.88),
            (r'\b(check.?in|check.?out|checkin|checkout)', 0.85),
            (r'\b(lodging|resort|guesthouse)', 0.80),
        ],
        'train': [
            (r'\b(book|want|need|search for)\s+(a\s+)?(train|railway|rail|ticket)', 0.95),
            (r'\b(train|railway|rail)\s+(from|to|on|for|between)', 0.90),
            # Match "train" when it appears after cities/keywords (e.g., "Mumbai to Delhi train")
            (r'\b(from|to|between)\s+[^.]+\s+(train|railway|rail)\b', 0.88),
            (r'\b\w+\s+(to|from)\s+\w+\s+(train|railway|rail)\b', 0.88),
            (r'\b(station|journey|platform|compartment)', 0.85),
            (r'\b(railway|locomotive)', 0.80),
            (r'\b(find|search|show|any)\s+trains?\b', 0.90),
            (r'\b(trains?)\s+(between|from)\b', 0.90),
            (r'\b(by\s+train|travel by train)\b', 0.85),
            (r'\b(tatkal|rac|waitlist|pnr|berth|sleeper|3ac|2ac|1ac|ac|non[-\s]?ac)\b', 0.85),
            (r'\b(rajdhani|shatabdi|vande bharat|garib rath)\b', 0.85),
            (r'\b(ndls|bct|mas|sbc)\b', 0.85),
            (r'\b(delhi)\s+to\s+(mumbai)\b', 0.80),
            (r'\b(bangalore)\s+to\s+(chennai)\b', 0.80),
        ]
    }
    
    def __init__(self):
        """Initialize intent rules."""
        self.pattern_matcher = PatternMatcher()
        self.station_aliases = self._load_station_aliases()
        self.city_aliases = self._load_city_aliases()

    def _load_station_aliases(self) -> set[str]:
        """Load station code aliases for intent detection."""
        data_dir = os.path.join(
            Path(__file__).parent.parent.parent.parent, 'src', 'data', 'entities'
        )
        try:
            aliases_file = os.path.join(data_dir, 'station_aliases.json')
            if os.path.exists(aliases_file):
                with open(aliases_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(k.lower() for k in data.get('aliases', {}).keys())
        except Exception:
            pass
        return set()

    def _load_city_aliases(self) -> set[str]:
        """Load city aliases for intent detection."""
        data_dir = os.path.join(
            Path(__file__).parent.parent.parent.parent, 'src', 'data', 'entities'
        )
        try:
            aliases_file = os.path.join(data_dir, 'city_aliases.json')
            if os.path.exists(aliases_file):
                with open(aliases_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(k.lower() for k in data.get('aliases', {}).keys())
        except Exception:
            pass
        return set()
    
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

        # Fallback: detect train intent from station codes
        if self.station_aliases:
            query_words = set(re.findall(r'\b[a-z0-9]+\b', query.lower()))
            if query_words.intersection(self.station_aliases):
                return {
                    'intent': 'train',
                    'confidence': 0.82,
                    'match_text': None
                }

        # Fallback: detect flight intent from city aliases (IATA codes)
        if self.city_aliases:
            query_words = set(re.findall(r'\b[a-z0-9]+\b', query.lower()))
            if len(query_words.intersection(self.city_aliases)) >= 2:
                return {
                    'intent': 'flight',
                    'confidence': 0.80,
                    'match_text': None
                }
        
        return None
    
    def get_all_intents(self) -> list[str]:
        """Get list of all supported intents."""
        return list(self.INTENT_PATTERNS.keys())
