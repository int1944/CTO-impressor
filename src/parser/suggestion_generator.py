"""Generates suggestions based on rule matches."""

from typing import List, Dict, Optional
from .rule_engine import RuleMatch
import os
import json
from pathlib import Path


class Suggestion:
    """Represents a single suggestion."""
    
    def __init__(self, text: str, entity_type: str, confidence: float, selectable: bool = True, is_placeholder: bool = False):
        """
        Initialize suggestion.
        
        Args:
            text: Suggestion text
            entity_type: Type of entity (slot name)
            confidence: Confidence score
            selectable: Whether this suggestion can be selected/clicked
            is_placeholder: Whether this is a placeholder (ghost text)
        """
        self.text = text
        self.entity_type = entity_type
        self.confidence = confidence
        self.selectable = selectable
        self.is_placeholder = is_placeholder
    
    def to_dict(self) -> Dict:
        """Convert suggestion to dictionary."""
        return {
            'text': self.text,
            'entity_type': self.entity_type,
            'confidence': self.confidence,
            'selectable': self.selectable,
            'is_placeholder': self.is_placeholder
        }


class SuggestionGenerator:
    """Generates suggestions based on rule matches."""
    
    # Placeholder text mapping for guidance
    PLACEHOLDER_MAP = {
        'from': 'from',
        'to': 'to where',
        'date': 'on which date',
        'time': 'at what time',
        'class': 'in which class',
        'airline': 'with which airline',
        'city': 'in which city',
        'checkin': 'check-in date',
        'checkout': 'check-out date',
        'guests': 'for how many guests',
        'rooms': 'how many rooms',
        'quota': 'which quota',
        'intent': None,  # No placeholder for intent
    }
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize suggestion generator.
        
        Args:
            data_dir: Directory containing entity data files
        """
        self.data_dir = data_dir or os.path.join(
            Path(__file__).parent.parent.parent, 'src', 'data', 'entities'
        )
        self.cities = self._load_cities()
        self.airlines = self._load_airlines()
        self.hotels = self._load_hotels()
    
    def _get_placeholder_text(self, slot: str, intent: Optional[str] = None) -> Optional[str]:
        """
        Get placeholder text for a given slot.
        
        Args:
            slot: Slot name (e.g., 'from', 'to', 'date')
            intent: Optional intent for context-specific placeholders
            
        Returns:
            Placeholder text or None if no placeholder
        """
        return self.PLACEHOLDER_MAP.get(slot)
    
    def _load_cities(self) -> List[str]:
        """Load city names."""
        try:
            cities_file = os.path.join(self.data_dir, 'cities.json')
            if os.path.exists(cities_file):
                with open(cities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('cities', [])
        except Exception:
            pass
        # Default cities if file doesn't exist
        return ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad']
    
    def _load_airlines(self) -> List[str]:
        """Load airline names."""
        try:
            airlines_file = os.path.join(self.data_dir, 'airlines.json')
            if os.path.exists(airlines_file):
                with open(airlines_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('airlines', [])
        except Exception:
            pass
        return ['IndiGo', 'Air India', 'SpiceJet', 'Vistara', 'GoAir']
    
    def _load_hotels(self) -> List[str]:
        """Load hotel names."""
        try:
            hotels_file = os.path.join(self.data_dir, 'hotels.json')
            if os.path.exists(hotels_file):
                with open(hotels_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('hotels', [])
        except Exception:
            pass
        return ['Taj', 'Oberoi', 'ITC', 'Marriott', 'Hilton']
    
    def generate(self, rule_match: RuleMatch, max_suggestions: int = 8, include_placeholder: bool = True) -> List[Suggestion]:
        """
        Generate suggestions based on rule match.
        
        Args:
            rule_match: Matched rule with intent and entities
            max_suggestions: Maximum number of suggestions to return
            include_placeholder: Whether to include placeholder as first suggestion
            
        Returns:
            List of suggestions (placeholder first if enabled, then entities)
        """
        if not rule_match:
            return []
        
        # Handle case where next_slot is None but we have a partial match
        if not rule_match.next_slot:
            # If intent is None but next_slot is 'intent', suggest intents
            if rule_match.intent is None:
                suggestions = self._get_intent_suggestions()
                return [
                    Suggestion(
                        text=s,
                        entity_type='intent',
                        confidence=rule_match.confidence,
                        selectable=True,
                        is_placeholder=False
                    )
                    for s in suggestions[:max_suggestions]
                ]
            return []
        
        result_suggestions = []
        next_slot = rule_match.next_slot
        intent = rule_match.intent
        entities = rule_match.entities
        
        # Add placeholder as first suggestion (non-selectable ghost text)
        if include_placeholder:
            placeholder_text = self._get_placeholder_text(next_slot, intent)
            if placeholder_text:
                result_suggestions.append(
                    Suggestion(
                        text=placeholder_text,
                        entity_type=next_slot,
                        confidence=rule_match.confidence,
                        selectable=False,
                        is_placeholder=True
                    )
                )
        
        # Generate entity suggestions based on next slot
        entity_suggestions = []
        if next_slot == 'intent':
            entity_suggestions = self._get_intent_suggestions()
        elif next_slot == 'from':
            entity_suggestions = self._get_city_suggestions(exclude=None)
        elif next_slot == 'to':
            # Exclude 'from' city if available
            from_city = None
            if entities.get('cities'):
                from_city = entities['cities'][0]
            entity_suggestions = self._get_city_suggestions(exclude=from_city)
        elif next_slot == 'date':
            entity_suggestions = self._get_date_suggestions()
        elif next_slot == 'time':
            entity_suggestions = self._get_time_suggestions()
        elif next_slot == 'class':
            entity_suggestions = self._get_class_suggestions(intent)
        elif next_slot == 'airline':
            entity_suggestions = self._get_airline_suggestions()
        elif next_slot == 'city':
            entity_suggestions = self._get_city_suggestions()
        elif next_slot == 'checkin' or next_slot == 'checkout':
            entity_suggestions = self._get_date_suggestions()
        elif next_slot == 'guests':
            entity_suggestions = self._get_guests_suggestions()
        elif next_slot == 'rooms':
            entity_suggestions = self._get_rooms_suggestions()
        elif next_slot == 'quota':
            entity_suggestions = self._get_quota_suggestions()
        
        # Add entity suggestions (selectable)
        # Adjust max_suggestions to account for placeholder
        entity_max = max_suggestions - (1 if include_placeholder and placeholder_text else 0)
        limited_entity_suggestions = entity_suggestions[:entity_max]
        
        for s in limited_entity_suggestions:
            result_suggestions.append(
                Suggestion(
                    text=s,
                    entity_type=next_slot,
                    confidence=rule_match.confidence,
                    selectable=True,
                    is_placeholder=False
                )
            )
        
        return result_suggestions
    
    def _get_intent_suggestions(self) -> List[str]:
        """Get intent suggestions."""
        return ['flight', 'hotel', 'train']
    
    def _get_city_suggestions(self, exclude: Optional[str] = None) -> List[str]:
        """Get city suggestions."""
        cities = self.cities.copy()
        if exclude:
            exclude_lower = exclude.lower()
            cities = [c for c in cities if c.lower() != exclude_lower]
        return cities[:10]  # Top 10 cities
    
    def _get_date_suggestions(self) -> List[str]:
        """Get date suggestions."""
        return ['today', 'tomorrow', 'this weekend', 'next week', 'next month']
    
    def _get_time_suggestions(self) -> List[str]:
        """Get time suggestions."""
        return ['morning', 'afternoon', 'evening', 'night']
    
    def _get_class_suggestions(self, intent: str) -> List[str]:
        """Get class suggestions."""
        if intent == 'flight':
            return ['economy', 'business', 'first', 'premium economy']
        elif intent == 'train':
            return ['sleeper', '3AC', '2AC', '1AC', 'general']
        return []
    
    def _get_airline_suggestions(self) -> List[str]:
        """Get airline suggestions."""
        return self.airlines[:8]
    
    def _get_guests_suggestions(self) -> List[str]:
        """Get guest count suggestions."""
        return ['1', '2', '3', '4', '5', '6']
    
    def _get_rooms_suggestions(self) -> List[str]:
        """Get room count suggestions."""
        return ['1', '2', '3', '4']
    
    def _get_quota_suggestions(self) -> List[str]:
        """Get quota suggestions for trains."""
        return ['general', 'tatkal', 'ladies', 'senior citizen']
