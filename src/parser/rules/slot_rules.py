"""Slot inference rules to determine what entity should come next."""

import re
from typing import Optional, Dict, List, Set
from .pattern_matcher import PatternMatcher


class SlotRules:
    """Rules for inferring the next slot to fill based on current query state."""
    
    # Slot order for each intent (core required slots only)
    SLOT_ORDER = {
        'flight': ['intent', 'from', 'to', 'date', 'time', 'class', 'airline'],
        'hotel': ['intent', 'city', 'checkin', 'checkout', 'guests', 'rooms'],
        'train': ['intent', 'from', 'to', 'date', 'class', 'quota'],
    }
    
    # Optional slots (suggested conditionally, not in strict order)
    OPTIONAL_SLOTS = {
        'flight': ['return', 'passengers'],
        'hotel': ['nights', 'category'],
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
        'nights': ['nights', 'night', 'days', 'day', 'for'],
        'category': ['star', 'stars', 'budget', 'luxury', 'deluxe', 'premium', 'category', 'rating'],
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
            from_index = query_lower.find(' from ')
            if from_index == -1:
                if query_lower.startswith('from '):
                    from_index = 0
                elif ' from' in query_lower:
                    from_index = query_lower.find(' from')
            
            if from_index != -1:
                # Get text after "from"
                if ' from ' in query_lower:
                    after_from = query_lower[from_index + 6:].strip()
                elif query_lower.startswith('from '):
                    after_from = query_lower[5:].strip()
                else:
                    after_from = query_lower[from_index + 5:].strip()
                
                # Only mark "from" as filled if there's a city after it
                if after_from and entities.get('cities'):
                    cities_after_from = [c for c in entities['cities'] if c.lower() in after_from]
                    if cities_after_from:
                        filled_slots.add('from')
        
        # Check for 'to' slot - only mark as filled if there's a city after "to"
        if self._has_slot_keyword(query_lower, 'to'):
            # Find "to" that comes after "from" (for flight/train queries)
            from_index = query_lower.find(' from ')
            if from_index == -1:
                from_index = query_lower.find('from ')
            
            if from_index != -1:
                # Look for "to" after "from"
                to_index = query_lower.find(' to ', from_index)
                if to_index == -1:
                    # Check if it ends with " to"
                    if query_lower.endswith(' to'):
                        # "to" is at end with no city after - don't mark as filled
                        pass
                    else:
                        to_index = query_lower.find(' to', from_index)
                
                if to_index != -1 and not query_lower.endswith(' to'):
                    # Get text after "to"
                    after_to = query_lower[to_index + 4:].strip() if ' to ' in query_lower[to_index:] else query_lower[to_index + 3:].strip()
                    # Only mark "to" as filled if there's a city after it
                    if after_to and entities.get('cities'):
                        cities_after_to = [c for c in entities['cities'] if c.lower() in after_to]
                        if cities_after_to:
                            filled_slots.add('to')
            else:
                # No "from" found, check if "to" has a city after it
                to_index = query_lower.find(' to ')
                if to_index != -1:
                    after_to = query_lower[to_index + 4:].strip()
                    if after_to and entities.get('cities'):
                        cities_after_to = [c for c in entities['cities'] if c.lower() in after_to]
                        if cities_after_to:
                            filled_slots.add('to')
        
        # Handle city-first scenarios: when cities appear before "from"/"to" keywords
        if entities.get('cities') and len(entities['cities']) >= 1:
            cities = entities['cities']
            
            # Find positions of keywords
            from_keyword_pos = query_lower.find(' from ')
            if from_keyword_pos == -1:
                if query_lower.startswith('from '):
                    from_keyword_pos = 0
                elif ' from' in query_lower:
                    from_keyword_pos = query_lower.find(' from')
            
            to_keyword_pos = query_lower.find(' to ')
            if to_keyword_pos == -1:
                if query_lower.startswith('to '):
                    to_keyword_pos = 0
                elif ' to' in query_lower and not query_lower.endswith(' to'):
                    to_keyword_pos = query_lower.find(' to')
            
            # Find positions of cities in query
            city_positions = []
            for city in cities:
                city_lower = city.lower()
                pos = query_lower.find(city_lower)
                if pos != -1:
                    city_positions.append((pos, city, city_lower))
            city_positions.sort()  # Sort by position in query
            
            # Case 1: City appears first, then "to" keyword appears
            # First city before "to" should be "from"
            if len(city_positions) >= 1 and to_keyword_pos != -1:
                first_city_pos, first_city, _ = city_positions[0]
                # If first city appears before "to" keyword and "from" not already filled
                if first_city_pos < to_keyword_pos and 'from' not in filled_slots:
                    # Check if "from" keyword exists - if yes, don't assume
                    if from_keyword_pos == -1:
                        # No "from" keyword, first city is "from"
                        filled_slots.add('from')
                    elif first_city_pos < from_keyword_pos:
                        # City appears before "from" keyword - it's still "from"
                        filled_slots.add('from')
            
            # Case 2: "to" keyword exists, check if city appears after it
            if to_keyword_pos != -1 and len(city_positions) >= 1:
                # Find city that appears after "to"
                for pos, city, city_lower in city_positions:
                    if pos > to_keyword_pos:
                        # City appears after "to" - mark as "to" slot
                        after_to = query_lower[to_keyword_pos + 4:].strip() if ' to ' in query_lower[to_keyword_pos:] else query_lower[to_keyword_pos + 3:].strip()
                        if city_lower in after_to:
                            filled_slots.add('to')
                            break
            
            # Case 3: "from" keyword exists, check if city appears after it
            if from_keyword_pos != -1 and len(city_positions) >= 1:
                # Find city that appears after "from" - that's the "from" city
                for pos, city, city_lower in city_positions:
                    if pos > from_keyword_pos:
                        after_from = query_lower[from_keyword_pos + 6:].strip() if ' from ' in query_lower[from_keyword_pos:] else query_lower[from_keyword_pos + 5:].strip()
                        if city_lower in after_from:
                            filled_slots.add('from')
                            break
                
                # If a city appears BEFORE "from" keyword, it's likely the destination ("to")
                # e.g., "Delhi from Mumbai" -> Delhi is "to", Mumbai is "from"
                for pos, city, city_lower in city_positions:
                    if pos < from_keyword_pos:
                        # City before "from" is likely "to" (destination)
                        filled_slots.add('to')
                        break
            
            # Case 4: No keywords, but cities exist - assume first is "from" (for flights/trains)
            if intent in ['flight', 'train']:
                if 'from' not in filled_slots and from_keyword_pos == -1 and to_keyword_pos == -1:
                    # No keywords at all, first city is likely "from"
                    if len(city_positions) >= 1:
                        filled_slots.add('from')
        
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
            if self._has_slot_keyword(query_lower, 'guests'):
                filled_slots.add('guests')
            if self._has_slot_keyword(query_lower, 'rooms'):
                filled_slots.add('rooms')
            # Check for nights slot
            if entities.get('nights') or self._has_slot_keyword(query_lower, 'nights'):
                filled_slots.add('nights')
            # Check for category slot
            if entities.get('category') or self._has_slot_keyword(query_lower, 'category'):
                filled_slots.add('category')
            # City slot for hotels
            if entities.get('cities'):
                filled_slots.add('city')
        elif intent == 'train':
            if self._has_slot_keyword(query_lower, 'quota'):
                filled_slots.add('quota')
        
        return filled_slots
    
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