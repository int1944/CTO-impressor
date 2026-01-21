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
            (r'\b(book|want|need|looking for|search for)\s+(a\s+)?(flight|flights|fly|airplane|airline|ticket)', 0.95),
            (r'\b(flight|flights|fly|flying|airline)\s+(from|to|on|for|between)', 0.90),
            # Match "flight" when it appears after cities/keywords (e.g., "Mumbai to Delhi flight")
            (r'\b(from|to|between)\s+[^.]+\s+(flight|flights|fly|flying)\b', 0.88),
            (r'\b\w+\s+(to|from)\s+\w+\s+(flight|flights|fly|flying)\b', 0.88),
            # Match standalone "flight" word (lower confidence to avoid false positives)
            (r'\b(flight|flights|fly|flying)\b', 0.78),
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
            (r'\b(book|want|need|looking for|search for)\s+(a\s+)?(hotel|hotels|stay|accommodation|room|reservation)', 0.95),
            (r'\b(hotel|hotels|stay|accommodation|room|booking)\s+(in|at|for|from|near|with)', 0.90),
            # Match "hotel" when it appears after cities/keywords (e.g., "Mumbai hotel")
            (r'\b\w+\s+(hotel|hotels|stay|accommodation|room)\b', 0.88),
            (r'\b(in|at|for)\s+[^.]+\s+(hotel|hotels|stay|accommodation)\b', 0.88),
            # Match "hotels with" pattern (e.g., "hotels with swimming pool")
            (r'\b(hotel|hotels)\s+with\b', 0.90),
            (r'\b(check.?in|check.?out|checkin|checkout)', 0.85),
            (r'\b(lodging|resort|guesthouse)', 0.80),
            (r'\b(find|search|show)\s+hotels?\b', 0.88),
            (r'\b(any\s+cheap|budget)\s+hotels?\b', 0.86),
            (r'\b(book a|book)\s+hotel\b', 0.85),
            (r'\b(hotel)\s+ticket\b', 0.80),
            (r'\b(by)\s+hotel\b', 0.78),
        ],
        'train': [
            (r'\b(book|want|need|search for)\s+(a\s+)?(train|trains|railway|rail|ticket)', 0.95),
            (r'\b(train|trains|railway|rail)\s+(from|to|on|for|between)', 0.90),
            # Match "train" when it appears after cities/keywords (e.g., "Mumbai to Delhi train")
            (r'\b(from|to|between)\s+[^.]+\s+(train|trains|railway|rail)\b', 0.88),
            (r'\b\w+\s+(to|from)\s+\w+\s+(train|trains|railway|rail)\b', 0.88),
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
            (r'\b(train)\s+ticket\b', 0.88),
            (r'\b(any\s+cheap|budget)\s+trains?\b', 0.86),
            (r'\b(tatkal)\s+ticket\b', 0.86),
        ],
        'holiday': [
            (r'\b(book|want|need|looking for|search for|plan)\s+(a\s+)?(holiday|holidays|vacation|package|trip|tour)', 0.95),
            (r'\b(holiday|holidays|vacation|package|trip|tour)\s+(to|for|starting|from)', 0.90),
            (r'\b(holiday|holidays|vacation)\s+package\b', 0.92),
            (r'\b(book|want|need)\s+(a\s+)?(holiday|holidays|vacation)\s+package\b', 0.95),
            (r'\b(plan|planning)\s+(a\s+)?(holiday|holidays|vacation|trip|tour)\b', 0.90),
            (r'\b(go\s+on|going\s+on)\s+(a\s+)?(vacation|holiday|holidays|trip)\b', 0.88),
            (r'\b(i\s+want\s+to\s+go\s+on|i\s+want\s+a)\s+(vacation|holiday|holidays)\b', 0.90),
            (r'\b(holiday|holidays|vacation)\s+to\s+[^\s]+\b', 0.88),
            (r'\b(week[-\s]?long|weekend|long\s+weekend)\s+(holiday|holidays|vacation|trip)\b', 0.85),
            (r'\b(\d+[-\s]?day|days?)\s+(holiday|holidays|vacation|trip|package)\b', 0.88),
            (r'\b(holiday|holidays|vacation)\s+for\s+(\d+)\s+(days?|nights?)\b', 0.88),
            # Romantic/Honeymoon/Getaway patterns - holiday packages
            (r'\b(romantic)\s+(getaway|trip|vacation|holiday|escape|retreat)\b', 0.95),
            (r'\b(honeymoon)\s*(trip|package|vacation|to|in|for|with)?\b', 0.95),
            (r'\b(couple|couples)\s+(trip|getaway|vacation|holiday|retreat)\b', 0.92),
            (r'\b(anniversary)\s+(trip|getaway|vacation|holiday|celebration)\b', 0.92),
            (r'\b(romantic|honeymoon|getaway|retreat|escape)\b', 0.85),
            (r'\b(beach|mountain|hill[-\s]?station|adventure|spiritual|wellness|spa)\s+(getaway|retreat|vacation|trip)\b', 0.88),
            (r'\b(family)\s+(vacation|holiday|trip|getaway|outing)\b', 0.90),
            (r'\b(solo)\s+(trip|travel|vacation|adventure)\b', 0.88),
            (r'\b(group)\s+(trip|tour|vacation|holiday)\b', 0.88),
            # Additional patterns for better coverage
            (r'\b(holiday|holidays|vacation|package|trip|tour)\b', 0.80),  # Standalone words (lower confidence)
            (r'\b(i\s+want|i\s+need|i\s+am\s+looking)\s+(a\s+)?(holiday|holidays|vacation|package)\b', 0.92),
            (r'\b(want|need|looking for)\s+(a\s+)?(holiday|holidays|vacation|package)\b', 0.90),
            (r'\b(book|book\s+me)\s+(a\s+)?(holiday|holidays|vacation|package|trip)\b', 0.93),
            (r'\b(holiday|holidays|vacation)\s+(package|trip|tour)\b', 0.90),
            (r'\b(travel|trip|tour)\s+(package|plan)\b', 0.85),
            # Patterns for queries without explicit "holiday/vacation" but with holiday context
            (r'\b(i\s+want\s+to\s+go\s+to|going\s+to|want\s+to\s+go)\s+[^\s]+\s+(next\s+month|next\s+week|next\s+weekend|tomorrow|starting|for\s+\d+)', 0.82),
            (r'\b(i\s+want\s+to\s+go|going|want\s+to\s+go)\s+to\s+[^\s]+\s+(with\s+my\s+family|for\s+family|for\s+\d+\s+days)', 0.80),
            # Standalone holiday/vacation words (lower confidence to avoid false positives)
            (r'^\s*(holiday|holidays|vacation|package|trip|tour)\s*$', 0.78),
            # More variations
            (r'\b(book|want|need)\s+(holiday|holidays|vacation|package|trip|tour)\b', 0.88),
            (r'\b(holiday|holidays|vacation|package)\s+(to|for|in)\b', 0.85),
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
