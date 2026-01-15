"""Slot inference rules to determine what entity should come next."""

import re
from typing import Optional, Dict, List, Set
from .pattern_matcher import PatternMatcher


class SlotRules:
    """Rules for inferring the next slot to fill based on current query state."""
    
    # Slot order for each intent
    SLOT_ORDER = {
        'flight': ['intent', 'from', 'to', 'date', 'time', 'class', 'airline'],
        'hotel': ['intent', 'city', 'checkin', 'checkout', 'guests', 'rooms'],
        'train': ['intent', 'from', 'to', 'date', 'class', 'quota'],
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
        
        # For flights and trains, prioritize "from" and "to" before "date"
        # But allow flexibility - if user provides date, we can accept it
        if intent in ['flight', 'train']:
            # Check if "from" is not filled
            if 'from' not in filled_slots:
                return 'from'
            # Check if "to" is not filled
            if 'to' not in filled_slots:
                return 'to'
        
        # Find first unfilled slot
        for slot in slot_order:
            if slot not in filled_slots:
                return slot
        
        return None  # All slots filled
    
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
        
        # If we have cities but no clear 'from'/'to', assume first is 'from'
        # But only if "from" keyword wasn't found or no city after it
        if entities.get('cities') and len(entities['cities']) >= 1:
            if 'from' not in filled_slots and not self._has_slot_keyword(query_lower, 'from'):
                # No "from" keyword, assume first city is "from"
                filled_slots.add('from')
            # Only mark "to" as filled if we have 2+ cities AND "to" keyword exists with city after it
            if len(entities['cities']) >= 2:
                if self._has_slot_keyword(query_lower, 'to'):
                    # Check if second city is after "to"
                    to_index = query_lower.find(' to ')
                    if to_index != -1:
                        after_to = query_lower[to_index + 4:].strip()
                        cities_after_to = [c for c in entities['cities'] if c.lower() in after_to]
                        if cities_after_to:
                            filled_slots.add('to')
        
        # Check for date slot
        if entities.get('dates'):
            filled_slots.add('date')
        
        # Check for time slot
        if entities.get('times'):
            filled_slots.add('time')
        
        # Check for class slot
        if entities.get('classes'):
            filled_slots.add('class')
        
        # Intent-specific slots
        if intent == 'flight':
            if entities.get('airlines'):
                filled_slots.add('airline')
        elif intent == 'hotel':
            if self._has_slot_keyword(query_lower, 'checkin') or entities.get('checkin'):
                filled_slots.add('checkin')
            if self._has_slot_keyword(query_lower, 'checkout') or entities.get('checkout'):
                filled_slots.add('checkout')
            if self._has_slot_keyword(query_lower, 'guests'):
                filled_slots.add('guests')
            if self._has_slot_keyword(query_lower, 'rooms'):
                filled_slots.add('rooms')
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
