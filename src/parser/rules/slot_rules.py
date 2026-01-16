"""Slot inference rules to determine what entity should come next."""

import re
from typing import Optional, Dict, List, Set
from .pattern_matcher import PatternMatcher


class SlotRules:
    """Rules for inferring the next slot to fill based on current query state."""
    
    # Slot order for each intent (core required slots only)
    SLOT_ORDER = {
        'flight': ['intent', 'from', 'to', 'date', 'time', 'class', 'airline'],
        'hotel': ['intent', 'city', 'checkin', 'checkout', 'nights', 'guests', 'room_type', 'category', 'rooms'],
        'train': ['intent', 'from', 'to', 'date', 'class', 'quota'],
    }
    
    # Optional slots (suggested conditionally, not in strict order)
    OPTIONAL_SLOTS = {
        'flight': ['return', 'passengers'],
        'hotel': ['nights', 'category', 'room_type', 'guests'],
        'train': ['passengers', 'time'],
    }
    
    # Keywords that indicate a slot is being filled
    SLOT_KEYWORDS = {
        'from': ['from', 'departure', 'depart', 'leaving', 'origin'],
        'to': ['to', 'destination', 'arrive', 'arrival', 'going'],
        'date': ['on', 'date', 'when', 'day'],
        'time': ['at', 'time', 'morning', 'afternoon', 'evening', 'night'],
        'class': ['class', 'economy', 'business', 'first'],
        'airline': ['airline', 'airlines', 'carrier'],
        'city': ['in', 'at', 'city', 'location', 'place'],
        'checkin': ['checkin', 'check-in', 'check in', 'arrival'],
        'checkout': ['checkout', 'check-out', 'check out', 'departure'],
        'guests': ['guests', 'guest', 'people', 'persons'],
        'rooms': ['room', 'rooms'],
        'quota': ['quota', 'tatkal', 'general'],
        'return': ['return', 'returning', 'coming back', 'round trip', 'round-trip'],
        'passengers': ['passengers', 'passenger', 'travelers', 'traveler', 'people', 'adults', 'adult'],
        'nights': ['nights', 'night', 'days', 'day'],
        'category': ['star', 'stars', 'budget', 'luxury', 'deluxe', 'premium', 'category', 'rating'],
        'room_type': ['single room', 'double room', 'suite', 'deluxe room'],
    }
    
    def __init__(self):
        """Initialize slot rules."""
        self.pattern_matcher = PatternMatcher()
    
    def infer(self, query: str, intent: str, entities: Dict) -> Optional[str]:
        """
        Infer the next slot that should be filled.
        
        Args:
            query: Current query text
            intent: Detected intent
            entities: Extracted entities
            
        Returns:
            Next slot name or None if all slots filled
        """
        if not intent or intent not in self.SLOT_ORDER:
            return 'intent'
        
        slot_order = self.SLOT_ORDER[intent]
        filled_slots = self._identify_filled_slots(query, intent, entities)

        # If user explicitly typed a slot keyword last, honor it (order-free)
        explicit_slot = self._get_last_keyword_slot(query, intent, filled_slots)
        if explicit_slot:
            return explicit_slot
        
        # For flights and trains, prioritize "from" and "to" before "date"
        # But allow flexibility - if user provides date, we can accept it
        if intent in ['flight', 'train']:
            # Check if "from" is not filled
            if 'from' not in filled_slots:
                return 'from'
            # Check if "to" is not filled
            if 'to' not in filled_slots:
                return 'to'
        
        # Find first unfilled core slot
        for slot in slot_order:
            if slot not in filled_slots:
                return slot
        
        # All core slots filled, check optional slots conditionally
        optional_slots = self.OPTIONAL_SLOTS.get(intent, [])
        for slot in optional_slots:
            if slot not in filled_slots:
                # Check if this optional slot should be suggested
                if self._should_suggest_optional_slot(slot, query, intent, entities, filled_slots):
                    return slot
        
        return None  # All slots filled

    def _get_last_keyword_slot(self, query: str, intent: str, filled_slots: Set[str]) -> Optional[str]:
        """Return the slot whose keyword appears last in the query."""
        query_lower = query.lower()
        last_slot = None
        last_index = -1
        
        # Only consider slots relevant for this intent
        valid_slots = set(self.SLOT_ORDER.get(intent, []))
        
        for slot, keywords in self.SLOT_KEYWORDS.items():
            if slot not in valid_slots:
                continue
            if slot in filled_slots:
                continue
            
            for keyword in keywords:
                match = re.search(r'\b' + re.escape(keyword) + r'\b', query_lower)
                if match:
                    idx = match.start()
                    if idx >= last_index:
                        last_index = idx
                        last_slot = slot
        
        return last_slot
    
    def _identify_filled_slots(self, query: str, intent: str, entities: Dict) -> Set[str]:
        """
        Identify which slots are already filled.
        
        Args:
            query: Query text
            intent: Detected intent
            entities: Extracted entities
            
        Returns:
            Set of filled slot names
        """
        filled_slots = set()
        query_lower = query.lower()
        
        # Check for intent (always filled if we got here)
        filled_slots.add('intent')
        
        # Check for 'from' slot - only mark as filled if there's a city after "from"
        if self._has_slot_keyword(query_lower, 'from'):
            if self._slot_has_city_after_keyword(query_lower, entities.get('cities', []), 'from'):
                filled_slots.add('from')
        
        # Check for 'to' slot - only mark as filled if there's a city after "to"
        if self._has_slot_keyword(query_lower, 'to'):
            if self._slot_has_city_after_keyword(query_lower, entities.get('cities', []), 'to'):
                filled_slots.add('to')
        
        # If we have cities but no clear 'from'/'to', assume first is 'from'
        # But only if "from" keyword wasn't found or no city after it
        if entities.get('cities') and len(entities['cities']) >= 1:
            if 'from' not in filled_slots and not self._has_slot_keyword(query_lower, 'from'):
                # No "from" keyword, assume first city is "from"
                filled_slots.add('from')
            # If we have 2+ cities, assume destination is also provided
            if len(entities['cities']) >= 2 and 'to' not in filled_slots:
                if self._has_slot_keyword(query_lower, 'to'):
                    # Check if any city is after "to"
                    if self._slot_has_city_after_keyword(query_lower, entities['cities'], 'to'):
                        filled_slots.add('to')
                else:
                    # No explicit "to" keyword, assume second city is destination
                    filled_slots.add('to')
        
        # Check for date slot
        if entities.get('dates'):
            filled_slots.add('date')
        
        # Check for time slot (only for flights and trains, not hotels)
        if entities.get('times') and intent in ['flight', 'train']:
            filled_slots.add('time')
        
        # Check for class slot
        if entities.get('classes'):
            filled_slots.add('class')
        
        # Check for passengers slot (flights and trains)
        if entities.get('passengers') and intent in ['flight', 'train']:
            filled_slots.add('passengers')
        
        # Intent-specific slots
        if intent == 'flight':
            if entities.get('airlines'):
                filled_slots.add('airline')
            # Check for return date slot
            if entities.get('return_dates') or self._has_slot_keyword(query_lower, 'return'):
                filled_slots.add('return')
        elif intent == 'hotel':
            if self._has_slot_keyword(query_lower, 'checkin') or entities.get('checkin'):
                filled_slots.add('checkin')
            if self._has_slot_keyword(query_lower, 'checkout') or entities.get('checkout'):
                filled_slots.add('checkout')
            if entities.get('guests') or self._has_slot_keyword(query_lower, 'guests') or self._has_for_number_guests(query_lower):
                filled_slots.add('guests')
            if self._has_slot_keyword(query_lower, 'rooms'):
                filled_slots.add('rooms')
            # Check for nights slot
            if entities.get('nights') or self._has_slot_keyword(query_lower, 'nights'):
                filled_slots.add('nights')
            # Check for category slot
            if entities.get('hotel_categories') or self._has_slot_keyword(query_lower, 'category'):
                filled_slots.add('category')
            # Check for room type slot
            if entities.get('room_types') or self._has_slot_keyword(query_lower, 'room_type'):
                filled_slots.add('room_type')
            # City slot for hotels
            if entities.get('cities'):
                filled_slots.add('city')
        elif intent == 'train':
            if self._has_slot_keyword(query_lower, 'quota'):
                filled_slots.add('quota')
        
        return filled_slots

    def _has_for_number_guests(self, query_lower: str) -> bool:
        """Detect 'for <number>' guest patterns without nights."""
        if re.search(r'\bfor\s+\d+\s+nights?\b', query_lower):
            return False
        return re.search(r'\bfor\s+\d+\b', query_lower) is not None

    def _slot_has_city_after_keyword(self, query_lower: str, cities: List[str], keyword: str) -> bool:
        """Check if any city appears after a slot keyword, regardless of order."""
        if not cities:
            return False
        
        keyword_pattern = r'\b' + re.escape(keyword) + r'\b'
        keyword_matches = list(re.finditer(keyword_pattern, query_lower))
        if not keyword_matches:
            return False
        
        city_patterns = []
        for city in cities:
            city_lower = city.lower()
            city_patterns.append((city_lower, re.compile(r'\b' + re.escape(city_lower) + r'\b')))
        
        for match in keyword_matches:
            after_text = query_lower[match.end():]
            for city_lower, pattern in city_patterns:
                if pattern.search(after_text):
                    return True
        
        return False
    
    def _has_slot_keyword(self, query: str, slot: str) -> bool:
        """Check if query contains keywords for a specific slot."""
        if slot not in self.SLOT_KEYWORDS:
            return False
        
        keywords = self.SLOT_KEYWORDS[slot]
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if self.pattern_matcher.match_pattern(query, pattern):
                return True
        
        return False
    
    def _should_suggest_optional_slot(self, slot: str, query: str, intent: str, entities: Dict, filled_slots: Set[str]) -> bool:
        """
        Check if an optional slot should be suggested.
        
        Args:
            slot: Optional slot name
            query: Query text
            intent: Detected intent
            entities: Extracted entities
            filled_slots: Set of already filled slots
            
        Returns:
            True if slot should be suggested, False otherwise
        """
        query_lower = query.lower()
        
        # Return slot: only suggest if round trip context detected
        if slot == 'return':
            # Check for round trip keywords
            round_trip_keywords = ['round trip', 'round-trip', 'return', 'returning', 'coming back']
            for keyword in round_trip_keywords:
                if keyword in query_lower:
                    return True
            # Don't suggest return if no round trip context
            return False
        
        # Passengers slot: suggest if explicitly mentioned or if keyword detected
        if slot == 'passengers':
            # Check if passengers keyword is explicitly mentioned
            if self._has_slot_keyword(query_lower, 'passengers'):
                return True
            # Check for "for [number] passengers/travelers" pattern
            passenger_patterns = [
                r'\bfor\s+\d+\s+(passengers?|travelers?|people|adults?)\b',
                r'\b\d+\s+(passengers?|travelers?|people|adults?)\b',
            ]
            for pattern in passenger_patterns:
                if self.pattern_matcher.match_pattern(query_lower, pattern):
                    return True
            # Don't suggest passengers unless explicitly mentioned
            return False
        
        # Nights slot: suggest if keyword detected or flexible placement
        if slot == 'nights':
            # Check if nights keyword is mentioned
            if self._has_slot_keyword(query_lower, 'nights'):
                return True
            # Check for "for [number] nights" pattern
            nights_pattern = r'\bfor\s+\d+\s+nights?\b'
            if self.pattern_matcher.match_pattern(query_lower, nights_pattern):
                return True
            # Can suggest nights after checkin is filled
            if 'checkin' in filled_slots:
                return True
            return False
        
        # Category slot: suggest if keyword detected, otherwise low priority
        if slot == 'category':
            # Check if category keyword is mentioned
            if self._has_slot_keyword(query_lower, 'category'):
                return True
            # Can suggest category after core slots are filled
            return True
        
        # Time slot for trains: suggest if keyword detected
        if slot == 'time' and intent == 'train':
            # Check if time keyword is mentioned
            if self._has_slot_keyword(query_lower, 'time'):
                return True
            # Can suggest time after date is filled
            if 'date' in filled_slots:
                return True
            return False
        
        # Default: suggest if keyword detected
        return self._has_slot_keyword(query_lower, slot)