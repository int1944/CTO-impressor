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
        
        # Check for 'from' slot
        if entities.get('cities') and self._has_slot_keyword(query_lower, 'from'):
            # Check if we can determine which city is 'from'
            # Simple heuristic: first city mentioned after 'from' keyword
            if self._has_slot_keyword(query_lower, 'from'):
                filled_slots.add('from')
        
        # Check for 'to' slot
        if entities.get('cities') and self._has_slot_keyword(query_lower, 'to'):
            filled_slots.add('to')
        
        # If we have cities but no clear 'from'/'to', assume first is 'from'
        if entities.get('cities') and len(entities['cities']) >= 1:
            if 'from' not in filled_slots:
                filled_slots.add('from')
            if len(entities['cities']) >= 2:
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
