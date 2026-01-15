"""Entity extraction rules for cities, dates, times, and intent-specific entities."""

import re
import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from .pattern_matcher import PatternMatcher


class EntityRules:
    """Rules for extracting entities from query text."""
    
    # Date patterns
    DATE_PATTERNS = [
        (r'\b(today|tonight)', 'today'),
        (r'\b(tomorrow|tmrw)', 'tomorrow'),
        (r'\b(day after tomorrow|day after)', 'day_after_tomorrow'),
        (r'\b(this\s+)?(weekend|sat|saturday|sun|sunday)', 'this_weekend'),
        (r'\b(next\s+)?(monday|mon|tuesday|tue|wednesday|wed|thursday|thu|friday|fri|saturday|sat|sunday|sun)', 'day_name'),
        (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', 'date_format'),  # DD/MM/YYYY or DD-MM-YYYY
        (r'\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)', 'date_named'),
    ]
    
    # Time patterns
    TIME_PATTERNS = [
        (r'\b(morning|am|a\.m\.)', 'morning'),
        (r'\b(afternoon|pm|p\.m\.)', 'afternoon'),
        (r'\b(evening)', 'evening'),
        (r'\b(night|late night)', 'night'),
        (r'\b(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?', 'time_format'),
    ]
    
    # Class patterns (for flights and trains)
    CLASS_PATTERNS = [
        (r'\b(economy|economy class)', 'economy'),
        (r'\b(business|business class)', 'business'),
        (r'\b(first|first class)', 'first'),
        (r'\b(premium economy|premium)', 'premium_economy'),
    ]
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize entity rules.
        
        Args:
            data_dir: Directory containing entity data files
        """
        self.pattern_matcher = PatternMatcher()
        self.data_dir = data_dir or os.path.join(
            Path(__file__).parent.parent.parent.parent, 'src', 'data', 'entities'
        )
        self.cities = self._load_cities()
        self.airlines = self._load_airlines()
        self.hotels = self._load_hotels()
    
    def _load_cities(self) -> List[str]:
        """Load city names from JSON file."""
        try:
            cities_file = os.path.join(self.data_dir, 'cities.json')
            if os.path.exists(cities_file):
                with open(cities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('cities', [])
        except Exception:
            pass
        return []
    
    def _load_airlines(self) -> List[str]:
        """Load airline names from JSON file."""
        try:
            airlines_file = os.path.join(self.data_dir, 'airlines.json')
            if os.path.exists(airlines_file):
                with open(airlines_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('airlines', [])
        except Exception:
            pass
        return []
    
    def _load_hotels(self) -> List[str]:
        """Load hotel names from JSON file."""
        try:
            hotels_file = os.path.join(self.data_dir, 'hotels.json')
            if os.path.exists(hotels_file):
                with open(hotels_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('hotels', [])
        except Exception:
            pass
        return []
    
    def extract(self, query: str, intent: Optional[str] = None) -> Dict[str, any]:
        """
        Extract entities from query.
        
        Args:
            query: Query text
            intent: Detected intent (optional, helps with context)
            
        Returns:
            Dict with extracted entities
        """
        entities = {
            'cities': [],
            'dates': [],
            'times': [],
            'classes': [],
            'airlines': [],
            'hotels': [],
        }
        
        # Extract cities
        entities['cities'] = self._extract_cities(query)
        
        # Extract dates
        entities['dates'] = self._extract_dates(query)
        
        # Extract times
        entities['times'] = self._extract_times(query)
        
        # Extract classes
        entities['classes'] = self._extract_classes(query)
        
        # Intent-specific extraction
        if intent == 'flight':
            entities['airlines'] = self._extract_airlines(query)
        elif intent == 'hotel':
            entities['hotels'] = self._extract_hotels(query)
        
        return entities
    
    def _extract_cities(self, query: str) -> List[str]:
        """Extract city names from query."""
        found_cities = []
        query_lower = query.lower()
        
        for city in self.cities:
            city_lower = city.lower()
            # Check for exact word match
            pattern = r'\b' + re.escape(city_lower) + r'\b'
            if self.pattern_matcher.match_pattern(query_lower, pattern):
                found_cities.append(city)
        
        return found_cities
    
    def _extract_dates(self, query: str) -> List[Dict[str, str]]:
        """Extract date expressions from query."""
        dates = []
        query_lower = query.lower()
        
        for pattern, date_type in self.DATE_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                dates.append({
                    'text': match.group(0),
                    'type': date_type,
                    'raw': match.group(0)
                })
        
        return dates
    
    def _extract_times(self, query: str) -> List[Dict[str, str]]:
        """Extract time expressions from query."""
        times = []
        query_lower = query.lower()
        
        for pattern, time_type in self.TIME_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                times.append({
                    'text': match.group(0),
                    'type': time_type,
                    'raw': match.group(0)
                })
        
        return times
    
    def _extract_classes(self, query: str) -> List[str]:
        """Extract class types from query."""
        classes = []
        query_lower = query.lower()
        
        for pattern, class_type in self.CLASS_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                classes.append(class_type)
        
        return classes
    
    def _extract_airlines(self, query: str) -> List[str]:
        """Extract airline names from query."""
        found_airlines = []
        query_lower = query.lower()
        
        for airline in self.airlines:
            airline_lower = airline.lower()
            pattern = r'\b' + re.escape(airline_lower) + r'\b'
            if self.pattern_matcher.match_pattern(query_lower, pattern):
                found_airlines.append(airline)
        
        return found_airlines
    
    def _extract_hotels(self, query: str) -> List[str]:
        """Extract hotel names from query."""
        found_hotels = []
        query_lower = query.lower()
        
        for hotel in self.hotels:
            hotel_lower = hotel.lower()
            pattern = r'\b' + re.escape(hotel_lower) + r'\b'
            if self.pattern_matcher.match_pattern(query_lower, pattern):
                found_hotels.append(hotel)
        
        return found_hotels
