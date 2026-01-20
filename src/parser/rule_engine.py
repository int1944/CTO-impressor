"""Main rule engine that orchestrates rule matching."""

import re
from typing import Optional, Dict
from .rules.intent_rules import IntentRules
from .rules.entity_rules import EntityRules
from .rules.slot_rules import SlotRules
from ..utils.cache import SimpleCache


class RuleMatch:
    """Represents a matched rule with extracted information."""
    
    def __init__(self, intent: str, confidence: float, entities: Dict, next_slot: Optional[str], match_text: Optional[str] = None):
        """
        Initialize rule match.
        
        Args:
            intent: Detected intent
            confidence: Confidence score (0.0 to 1.0)
            entities: Extracted entities
            next_slot: Next slot to fill
            match_text: Matched text from pattern
        """
        self.intent = intent
        self.confidence = confidence
        self.entities = entities
        self.next_slot = next_slot
        self.match_text = match_text


class RuleEngine:
    """Main rule matching engine."""
    
    def __init__(self, data_dir: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize rule engine.
        
        Args:
            data_dir: Directory containing entity data files
            enable_cache: Whether to enable caching
        """
        self.intent_rules = IntentRules()
        self.entity_rules = EntityRules(data_dir)
        self.slot_rules = SlotRules()
        self.cache = SimpleCache(ttl_seconds=300) if enable_cache else None
    
    def match(self, query: str, context: Optional[Dict] = None) -> Optional[RuleMatch]:
        """
        Match query against rules.
        
        Args:
            query: User query text
            context: Optional context dictionary
            
        Returns:
            RuleMatch if rules matched, None otherwise
        """
        if not query or not query.strip():
            print("No query provided")
            return None
        
        # Check cache
        if self.cache:
            cached = self.cache.get(query)
            if cached:
                print("Cache hit")
                return cached
        
        # Try intent rules first
        intent_match = self.intent_rules.match(query)
        
        if intent_match:
            intent = intent_match['intent']
            confidence = intent_match['confidence']
            match_text = intent_match.get('match_text')
            
            # Extract entities
            entities = self.entity_rules.extract(query, intent)
            
            # Infer next slot
            next_slot = self.slot_rules.infer(query, intent, entities)
            
            rule_match = RuleMatch(
                intent=intent,
                confidence=confidence,
                entities=entities,
                next_slot=next_slot,
                match_text=match_text
            )
            
            # Cache result
            if self.cache:
                self.cache.set(query, rule_match)
            
            return rule_match
        
        # Check for partial intent patterns (e.g., "I want to book a" -> suggest intents)
        partial_match = self._match_partial_intent(query)
        if partial_match:
            return partial_match
        
        # Check for city-first or from-first queries (without intent)
        city_from_match = self._match_city_or_from_first(query)
        if city_from_match:
            return city_from_match
        
        # Check for date-first queries (without intent)
        # e.g., "weekend for 2", "tomorrow for 2 passengers"
        date_first_match = self._match_date_first(query)
        if date_first_match:
            return date_first_match
        
        # No match found
        # print("No match found")  # Commented out - normal behavior when using LLM fallback
        return None
    
    def _match_partial_intent(self, query: str) -> Optional[RuleMatch]:
        """
        Match partial queries that suggest an intent is coming.
        E.g., "I want to book a" -> suggest flight/hotel/train
        """
        query_lower = query.lower().strip()
        
        # Simple string matching - check if query ends with patterns that suggest intent is coming
        # Order matters - check longer patterns first
        partial_endings = [
            'want to book a',
            'need to book a',
            'looking for a',
            'search for a',
            'book me a',
            'book me',
            'want to book',
            'need to book',
            'book a',
            'want a',
            'need a',
            'book',
            'want',
            'need',
        ]
        
        # Check if query ends with any partial pattern
        for ending in partial_endings:
            if query_lower.endswith(ending):
                return RuleMatch(
                    intent=None,  # No intent yet, but we know they're about to specify one
                    confidence=0.5,
                    entities={},
                    next_slot='intent',
                    match_text=None
                )
        
        # Also check for queries that start with booking intent but don't have an intent word yet
        if query_lower.startswith(('i want', 'i need', 'i am looking', 'want', 'need')):
            # If no intent word is present, suggest intents
            if not any(word in query_lower for word in ['flight', 'hotel', 'train', 'cab', 'ticket', 'airline', 'accommodation', 'stay']):
                return RuleMatch(
                    intent=None,
                    confidence=0.4,
                    entities={},
                    next_slot='intent',
                    match_text=None
                )
        
        return None
    
    def _match_city_or_from_first(self, query: str) -> Optional[RuleMatch]:
        """
        Match queries that start with a city or "from" keyword, even without intent.
        E.g., "Mumbai" -> suggest "to where"
        E.g., "from Mumbai" -> suggest "to where"
        E.g., "Mumbai to" -> suggest destination cities
        """
        if not query or not query.strip():
            return None
        
        query_lower = query.lower().strip()
        query_stripped = query.strip()
        
        # Extract entities (cities) even without intent
        entities = self.entity_rules.extract(query, intent=None)
        cities = entities.get('cities', [])
        
        if not cities:
            return None
        
        # Check if query starts with "from" keyword
        if query_lower.startswith('from '):
            # Check if "to" keyword appears after "from city"
            after_from = query_lower[5:].strip()  # After "from "
            
            # Find where the city ends
            first_city_lower = cities[0].lower()
            city_end_in_after_from = after_from.find(first_city_lower) + len(first_city_lower) if first_city_lower in after_from else 0
            remaining_after_city = after_from[city_end_in_after_from:].strip() if city_end_in_after_from > 0 else after_from
            
            if remaining_after_city.startswith('to ') or remaining_after_city.startswith('to'):
                # Check if there's a second city after "to"
                after_to = remaining_after_city[3:].strip() if remaining_after_city.startswith('to ') else remaining_after_city[2:].strip()
                
                # Check if any city (other than the first) appears after "to"
                has_second_city = False
                for city in cities:
                    city_lower = city.lower()
                    if city_lower != first_city_lower and city_lower in after_to:
                        has_second_city = True
                        break
                
                if has_second_city:
                    # "from Mumbai to Delhi" -> both cities present, suggest intent
                    return RuleMatch(
                        intent=None,
                        confidence=0.6,
                        entities=entities,
                        next_slot='intent',
                        match_text=None
                    )
                else:
                    # "from Mumbai to" -> suggest destination cities
                    return RuleMatch(
                        intent=None,
                        confidence=0.6,
                        entities=entities,
                        next_slot='to',
                        match_text=None
                    )
            else:
                # "from Mumbai" -> suggest "to" (destination)
                return RuleMatch(
                    intent=None,
                    confidence=0.6,
                    entities=entities,
                    next_slot='to',
                    match_text=None
                )
        
        # Check if query starts with a city name
        first_city = cities[0]
        first_city_lower = first_city.lower()
        
        # Check if query starts with the first city
        if query_lower.startswith(first_city_lower):
            # Check if "to" keyword appears after the city
            city_end_pos = len(first_city)
            remaining_query = query_stripped[city_end_pos:].strip()
            remaining_lower = remaining_query.lower()
            
            if remaining_lower.startswith('to ') or remaining_lower.startswith('to'):
                # Check if there's a second city after "to"
                after_to = remaining_lower[3:].strip() if remaining_lower.startswith('to ') else remaining_lower[2:].strip()
                
                # Check if any city (other than the first) appears after "to"
                has_second_city = False
                for city in cities:
                    city_lower = city.lower()
                    if city_lower != first_city_lower and city_lower in after_to:
                        has_second_city = True
                        break
                
                if has_second_city:
                    # "Mumbai to Delhi" -> both cities present, suggest intent
                    return RuleMatch(
                        intent=None,
                        confidence=0.6,
                        entities=entities,
                        next_slot='intent',
                        match_text=None
                    )
                else:
                    # "Mumbai to" -> suggest destination cities
                    return RuleMatch(
                        intent=None,
                        confidence=0.6,
                        entities=entities,
                        next_slot='to',
                        match_text=None
                    )
            else:
                # "Mumbai" (just city) -> suggest "to" (destination)
                return RuleMatch(
                    intent=None,
                    confidence=0.5,
                    entities=entities,
                    next_slot='to',
                    match_text=None
                )
        
        # Check if query contains "from city" pattern (e.g., "Delhi from Mumbai")
        if ' from ' in query_lower:
            from_index = query_lower.find(' from ')
            before_from = query_lower[:from_index].strip()
            after_from = query_lower[from_index + 6:].strip()
            
            # Check if a city appears before "from" and after "from"
            city_before_from = False
            city_after_from = False
            
            for city in cities:
                city_lower = city.lower()
                if city_lower in before_from:
                    city_before_from = True
                if city_lower in after_from:
                    city_after_from = True
            
            if city_before_from and city_after_from:
                # "Delhi from Mumbai" -> both cities present, suggest intent
                return RuleMatch(
                    intent=None,
                    confidence=0.6,
                    entities=entities,
                    next_slot='intent',
                    match_text=None
                )
        
        return None
    
    def _match_date_first(self, query: str) -> Optional[RuleMatch]:
        """
        Match queries that start with a date, even without intent.
        E.g., "weekend for 2" -> suggest intent or next slot
        E.g., "tomorrow for 2 passengers" -> suggest intent or next slot
        """
        if not query or not query.strip():
            return None
        
        query_lower = query.lower().strip()
        
        # Extract entities (dates, passengers, nights) even without intent
        entities = self.entity_rules.extract(query, intent=None)
        dates = entities.get('dates', [])
        passengers = entities.get('passengers', [])
        nights = entities.get('nights', [])
        
        # Check if query starts with a date word
        date_keywords = ['today', 'tomorrow', 'weekend', 'monday', 'tuesday', 'wednesday', 
                        'thursday', 'friday', 'saturday', 'sunday', 'next week', 'next month']
        
        starts_with_date = False
        for date_kw in date_keywords:
            if query_lower.startswith(date_kw):
                starts_with_date = True
                break
        
        # Also check if dates were extracted
        if dates and not starts_with_date:
            # Check if date appears early in the query
            first_date = dates[0]
            date_text = first_date.get('text', '').lower()
            if date_text and query_lower.find(date_text) < 10:  # Date appears in first 10 chars
                starts_with_date = True
        
        if not starts_with_date:
            return None
        
        # If we have date + passengers/nights, suggest intent
        if (passengers or nights) and dates:
            return RuleMatch(
                intent=None,
                confidence=0.6,
                entities=entities,
                next_slot='intent',
                match_text=None
            )
        
        # If we have date + "for [number]", check what "for" refers to
        if dates and ' for ' in query_lower:
            # Check if "for" is followed by a number (could be passengers or nights)
            for_match = re.search(r'\bfor\s+(\d+)(?:\s+(passengers?|travelers?|people|nights?|days?))?', query_lower)
            if for_match:
                # If it's "for [number]" without specifying, suggest intent
                return RuleMatch(
                    intent=None,
                    confidence=0.6,
                    entities=entities,
                    next_slot='intent',
                    match_text=None
                )
        
        # If we just have a date, suggest intent
        if dates:
            return RuleMatch(
                intent=None,
                confidence=0.5,
                entities=entities,
                next_slot='intent',
                match_text=None
            )
        
        return None