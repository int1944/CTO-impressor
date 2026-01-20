"""Entity extraction rules for cities, dates, times, and intent-specific entities."""

import re
import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from .pattern_matcher import PatternMatcher
from src.services.city_service import get_city_service


class EntityRules:
    """Rules for extracting entities from query text."""
    
    # Date patterns
    DATE_PATTERNS = [
        (r'\b(today|tonight)', 'today'),
        (r'\b(tomorrow|tmrw)', 'tomorrow'),
        (r'\b(yesterday)\b', 'yesterday'),
        (r'\b(day after tomorrow|day after)', 'day_after_tomorrow'),
        (r'\b(this\s+)?(weekend|sat|saturday|sun|sunday)', 'this_weekend'),
        (r'\b(next\s+)?(monday|mon|tuesday|tue|wednesday|wed|thursday|thu|friday|fri|saturday|sat|sunday|sun)', 'day_name'),
        (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', 'date_format'),  # DD/MM/YYYY or DD-MM-YYYY
        (r'\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)', 'date_named'),
        (r'\b(\d{1,2})(st|nd|rd|th)\b', 'day_ordinal'),
        (r'\b(aaj)\b', 'today'),
        (r'\b(kal)\b', 'relative_day'),
    ]

    HOTEL_NIGHTS_PATTERNS = [
        (r'\b(\d+)\s+nights?\b', 'nights'),
        (r'\b(for)\s+(\d+)\s+nights?\b', 'nights'),
    ]

    HOTEL_GUESTS_PATTERNS = [
        (r'\bwith\s+(\d+)\s+guests?\b', 'guests'),
        (r'\bwith\s+(\d+)\s+people\b', 'guests'),
        (r'\b(\d+)\s+guests?\b', 'guests'),
        (r'\b(\d+)\s+people\b', 'guests'),
        (r'\bfor\s+(\d+)\s+guests?\b', 'guests'),  # "for 3 guests" - explicit
        (r'\bfor\s+(\d+)\s+people\b', 'guests'),  # "for 3 people" - explicit
        (r'\b(with\s+family|with my family|staying with family)\b', 'guests_implicit'),
        # Note: "for [number]" without "nights" or "guests" is ambiguous - don't mark as guests
    ]

    HOTEL_ROOM_TYPE_PATTERNS = [
        (r'\b(single room|double room|suite|deluxe room)\b', 'room_type'),
        (r'\b(room)\s+(type)\b', 'room_type'),
    ]

    HOTEL_CATEGORY_PATTERNS = [
        (r'\b(\d)\s*-\s*star\b', 'category'),
        (r'\b(\d)\s*star\b', 'category'),
        (r'\b(luxury|budget|affordable)\s+hotels?\b', 'category'),
        (r'\b(5-star|4-star|3-star|2-star|1-star)\b', 'category'),
    ]

    # Holiday-specific patterns
    HOLIDAY_THEME_PATTERNS = [
        (r'\b(honeymoon|romantic|couple)\b', 'honeymoon'),
        (r'\b(adventure|trekking|hiking|mountaineering)\b', 'adventure'),
        (r'\b(beach|seaside|coastal|island)\b', 'beach'),
        (r'\b(family|kids|children|with family)\b', 'family'),
        (r'\b(mountains?|hill station|hills?)\b', 'mountains'),
        (r'\b(cultural|heritage|historical|temple|religious)\b', 'cultural'),
        (r'\b(wildlife|safari|jungle)\b', 'wildlife'),
        (r'\b(spiritual|pilgrimage|yoga|meditation)\b', 'spiritual'),
    ]

    HOLIDAY_BUDGET_PATTERNS = [
        (r'\b(under|within|less than|below)\s+(₹|rs\.?|inr|usd|eur|\$)?\s*\d+[,\d]*\b', 'budget_max'),
        (r'\b(budget|economy|affordable|cheap)\b', 'budget_low'),
        (r'\b(luxury|premium|deluxe|high-end)\b', 'budget_high'),
        (r'\b(mid-range|moderate|standard)\b', 'budget_mid'),
    ]

    HOLIDAY_DURATION_PATTERNS = [
        (r'\b(for\s+)?(\d+)\s+(days?|nights?)\b', 'duration_days'),
        (r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(days?|nights?)\b', 'duration_word'),
        (r'\b(\d+)[-\s]?day\s+(holiday|vacation|package|trip)\b', 'duration_day'),
        (r'\b(week[-\s]?long|weekend|long\s+weekend)\b', 'duration_week'),
    ]

    DATE_RANGE_PATTERNS = [
        (r'\b(between|from)\s+(.+?)\s+(and|to)\s+(.+?)\b', 'date_range'),
        (r'\b(\d{1,2})(st|nd|rd|th)?\s+to\s+(\d{1,2})(st|nd|rd|th)?\b', 'date_range'),
        (r'\b(returning\s+after\s+(a\s+week|\d+\s+days))\b', 'return_after'),
        (r'\b(coming\s+back\s+in\s+\d+\s+days)\b', 'return_after'),
        (r'\b(around|about)\s+(.+?)\b', 'date_flexible'),
        (r'\b(next\s+week|next\s+month|this\s+month|first\s+half\s+of\s+\w+)\b', 'date_flexible'),
        (r'\b(sometime\s+next\s+month|around\s+christmas)\b', 'date_flexible'),
        (r'\b(after\s+(holi|diwali|eid|christmas))\b', 'date_flexible'),
    ]
    
    # Time patterns
    TIME_PATTERNS = [
        (r'\b(morning|am|a\.m\.)', 'morning'),
        (r'\b(afternoon|pm|p\.m\.)', 'afternoon'),
        (r'\b(evening)', 'evening'),
        (r'\b(night|late night)', 'night'),
        (r'\b(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?', 'time_format'),
        (r'\b(subah)\b', 'morning'),
        (r'\b(raat)\b', 'night'),
    ]

    TIME_PREFERENCE_PATTERNS = [
        (r'\b(early\s+morning|red[-\s]?eye)\b', 'time_preference'),
        (r'\b(before\s+\w+|after\s+\w+)\b', 'time_window'),
        (r'\b(before\s+\d{1,2}\s*(am|pm)|after\s+\d{1,2}\s*(am|pm)|after\s+\d{1,2}\s*pm|before\s+noon|after\s+\d{1,2}\s*pm\s+only)\b', 'time_window'),
        (r'\b(night train|overnight trains|morning departure)\b', 'time_preference'),
        (r'\b(trains?\s+after\s+\d{1,2}\s*pm|after\s+\d{1,2}\s*pm)\b', 'time_window'),
    ]

    PRICE_PATTERNS = [
        (r'\b(under|within|less than)\s+(₹|rs\.?|inr|usd|eur|\$)?\s*\d+[,\d]*\b', 'price_max'),
        (r'\b(cheapest|lowest fare|budget|cheaper options|cheaper alternative date|cheapest seat)\b', 'price_sort'),
        (r'\b(fare|ticket price|tatkal fare)\b', 'fare_query'),
    ]

    PASSENGER_PATTERNS = [
        (r'\b(\d+)\s+adults?\b', 'adults'),
        (r'\b(\d+)\s+children?\b', 'children'),
        (r'\b(\d+)\s+infants?\b', 'infants'),
        (r'\b(just me|only me|it\'?s just me|me and my wife|me and my husband|me and my partner|traveling with my family|with my family)\b', 'passenger_group'),
        (r'\b(add one more passenger|one more passenger|zero passengers|0 passengers)\b', 'passenger_update'),
        (r'\b(family of\s+\d+)\b', 'passenger_group'),
        (r'\b(me and my parents)\b', 'passenger_group'),
        (r'\b(senior citizen)\b', 'senior'),
        (r'\b(\d{1,2})\s+years old\b', 'age'),
        (r'\b(age|aged)\s+\d{1,2}\b', 'age'),
    ]

    STOP_PATTERNS = [
        (r'\b(non[-\s]?stop|direct)\b', 'nonstop'),
        (r'\b(one stop|1 stop|single stop)\b', 'one_stop'),
        (r'\b(no more than one stop|not more than one stop)\b', 'max_one_stop'),
        (r'\b(one stop but not more)\b', 'max_one_stop'),
        (r'\b(shortest travel time|shortest duration|avoid long layovers)\b', 'duration_preference'),
        (r'\b(fastest train|express trains only|avoid passenger trains)\b', 'speed_preference'),
    ]

    BAGGAGE_PATTERNS = [
        (r'\b(free check[-\s]?in baggage|free baggage)\b', 'free_checked_baggage'),
        (r'\b(only cabin baggage|carry[-\s]?on only)\b', 'cabin_only'),
        (r'\b(\d+)\s+bags?\b', 'bag_count'),
        (r'\b(paid luggage|avoid airlines with paid luggage)\b', 'avoid_paid_luggage'),
    ]

    BERTH_PATTERNS = [
        (r'\b(lower berth|side lower|upper berth|side upper|window seat|side lower seat)\b', 'berth_preference'),
        (r'\b(any berth is fine)\b', 'berth_any'),
    ]

    QUOTA_PATTERNS = [
        (r'\b(tatkal|ladies quota|senior citizen quota|general quota|defence quota)\b', 'quota'),
    ]

    AVAILABILITY_PATTERNS = [
        (r'\b(waitlist|rac|availability|available|is sleeper available)\b', 'availability'),
    ]

    TRAIN_NAME_PATTERNS = [
        (r'\b(rajdhani|shatabdi|vande bharat|garib rath)\b', 'train_name'),
    ]

    PNR_PATTERNS = [
        (r'\b(pnr|pnr status)\b', 'pnr'),
        (r'\b(seat number|coach number|ticket confirmed)\b', 'pnr_detail'),
    ]

    AIRLINE_PREFERENCE_PATTERNS = [
        (r'\b(only with|prefer|I prefer|any)\s+([a-zA-Z ]+)\b', 'airline_prefer'),
        (r'\b(avoid|no)\s+(budget airlines|[a-zA-Z ]+)\b', 'airline_avoid'),
    ]

    LOYALTY_PATTERNS = [
        (r'\b(use my miles|miles|loyalty points|star alliance points)\b', 'loyalty'),
    ]

    SPECIAL_NEEDS_PATTERNS = [
        (r'\b(wheelchair assistance|traveling with a pet|pet|unaccompanied minor|special meal required|special meal)\b', 'special_needs'),
    ]

    TRIP_TYPE_PATTERNS = [
        (r'\b(round\s*trip|round-trip|return flight|returning|coming back)\b', 'round_trip'),
        (r'\b(multi[-\s]?city|two[-\s]?city|three[-\s]?city)\b', 'multi_city'),
        (r'\b(one[-\s]?way)\b', 'one_way'),
    ]

    ACTION_PATTERNS = [
        (r'\b(book|reserve|confirm|go ahead|proceed)\b', 'book'),
        (r'\b(hold|decide later)\b', 'hold'),
        (r'\b(cancel|refund|cancellation fee)\b', 'cancel'),
        (r'\b(change date|reschedule|modify)\b', 'change'),
        (r'\b(payment|pay with|upi|card|split payment)\b', 'payment'),
        (r'\b(status|terminal|layover duration|food included)\b', 'info'),
    ]
    
    # Class patterns (for flights and trains)
    CLASS_PATTERNS = [
        (r'\b(economy|economy class)', 'economy'),
        (r'\b(business|business class)', 'business'),
        (r'\b(first|first class)', 'first'),
        (r'\b(premium economy|premium)', 'premium_economy'),
        (r'\b(sleeper|sl)\b', 'sleeper'),
        (r'\b(3ac|three ac|3 ac)\b', '3ac'),
        (r'\b(2ac|two ac|2 ac)\b', '2ac'),
        (r'\b(1ac|first ac|1 ac)\b', '1ac'),
        (r'\b(ac|ac coach|ac only)\b', 'ac'),
        (r'\b(non[-\s]?ac)\b', 'non_ac'),
        (r'\b(general|second class|2s)\b', 'general'),
        (r'\b(chair car|cc)\b', 'chair_car'),
        (r'\b(any class|any class is fine)\b', 'any'),
    ]
    
    # Return date patterns (for flights)
    RETURN_DATE_PATTERNS = [
        (r'\b(return|returning|coming back|round trip)\s+(on|by|before|after)?\s*(.+?)\b', 'return_date'),
        (r'\b(return|returning)\s+(tomorrow|today|next week|next month)\b', 'return_date'),
        (r'\b(return|returning)\s+on\s+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', 'return_date'),
        (r'\b(return|returning)\s+on\s+(\d{1,2})(st|nd|rd|th)\b', 'return_date'),
    ]
    
    # Nights patterns (for hotels)
    NIGHTS_PATTERNS = [
        (r'\b(for\s+)?(\d+)\s+(nights?|days?)\b', 'nights'),
        (r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(nights?|days?)\b', 'nights'),
        (r'\b(\d+)\s+night\s+stay\b', 'nights'),
    ]
    
    # Category/Property class patterns (for hotels)
    CATEGORY_PATTERNS = [
        (r'\b(\d)\s*star\s*(hotel|property)?\b', 'star_rating'),
        (r'\b(5[-\s]?star|4[-\s]?star|3[-\s]?star|2[-\s]?star|1[-\s]?star)\b', 'star_rating'),
        (r'\b(budget|economy|mid-range|luxury|deluxe|premium)\s*(hotel)?\b', 'category'),
        (r'\b(boutique|resort|apartment|villa)\b', 'category'),
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
        # Use CityService for cities
        self.city_service = get_city_service()
        self.cities = self._load_cities()  # Keep for backward compatibility
        self.city_aliases = self._load_city_aliases()
        self.station_aliases = self._load_station_aliases()
        self.airlines = self._load_airlines()
        self.hotels = self._load_hotels()
    
    def _load_cities(self) -> List[str]:
        """Load city names (for backward compatibility)."""
        # Use CityService to get all cities
        cities = self.city_service.get_all_cities()
        if cities:
            return cities
        
        # Fallback to JSON if CityService has no cities
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

    def _load_city_aliases(self) -> Dict[str, str]:
        """Load city aliases (IATA codes, abbreviations) from JSON file."""
        try:
            aliases_file = os.path.join(self.data_dir, 'city_aliases.json')
            if os.path.exists(aliases_file):
                with open(aliases_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {k.lower(): v for k, v in data.get('aliases', {}).items()}
        except Exception:
            pass
        return {}

    def _load_station_aliases(self) -> Dict[str, str]:
        """Load station code aliases from JSON file."""
        try:
            aliases_file = os.path.join(self.data_dir, 'station_aliases.json')
            if os.path.exists(aliases_file):
                with open(aliases_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {k.lower(): v for k, v in data.get('aliases', {}).items()}
        except Exception:
            pass
        return {}
    
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
            'date_ranges': [],
            'time_preferences': [],
            'price_constraints': [],
            'passengers': [],
            'stops': [],
            'baggage': [],
            'trip_type': [],
            'actions': [],
            'airline_preferences': [],
            'loyalty': [],
            'special_needs': [],
            'berths': [],
            'quota': [],
            'availability': [],
            'train_names': [],
            'stations': [],
            'pnr': [],
            'nights': [],
            'guests': [],
            'room_types': [],
            'hotel_categories': [],
            'times': [],
            'classes': [],
            'airlines': [],
            'hotels': [],
            'themes': [],
            'budgets': [],
        }
        
        # Extract cities
        entities['cities'] = self._extract_cities(query)

        # Extract station codes
        entities['stations'] = self._extract_station_codes(query)
        
        # Extract dates
        entities['dates'] = self._extract_dates(query)

        # Extract date ranges / flexibility
        entities['date_ranges'] = self._extract_date_ranges(query)
        
        # Extract times
        entities['times'] = self._extract_times(query)

        # Extract time preferences
        entities['time_preferences'] = self._extract_time_preferences(query)
        
        # Extract classes
        entities['classes'] = self._extract_classes(query)

        # Extract price constraints
        entities['price_constraints'] = self._extract_price_constraints(query)

        # Extract passengers
        entities['passengers'] = self._extract_passengers(query)

        # Extract stop preferences
        entities['stops'] = self._extract_stops(query)

        # Extract baggage preferences
        entities['baggage'] = self._extract_baggage(query)

        # Extract trip type
        entities['trip_type'] = self._extract_trip_type(query)

        # Extract booking actions / info intent
        entities['actions'] = self._extract_actions(query)

        # Extract airline preferences
        entities['airline_preferences'] = self._extract_airline_preferences(query)

        # Extract loyalty preferences
        entities['loyalty'] = self._extract_loyalty(query)

        # Extract special needs
        entities['special_needs'] = self._extract_special_needs(query)

        # Extract berth preferences
        entities['berths'] = self._extract_berths(query)

        # Extract quota preferences
        entities['quota'] = self._extract_quota(query)

        # Extract availability/status queries
        entities['availability'] = self._extract_availability(query)

        # Extract train name preferences
        entities['train_names'] = self._extract_train_names(query)

        # Extract PNR/status details
        entities['pnr'] = self._extract_pnr(query)

        # Extract hotel-specific entities
        entities['nights'] = self._extract_hotel_nights(query)
        entities['guests'] = self._extract_hotel_guests(query)
        entities['room_types'] = self._extract_hotel_room_types(query)
        entities['hotel_categories'] = self._extract_hotel_categories(query)
        
        # Intent-specific extraction
        if intent == 'flight':
            entities['airlines'] = self._extract_airlines(query)
        elif intent == 'hotel':
            entities['hotels'] = self._extract_hotels(query)
        elif intent == 'holiday':
            entities['themes'] = self._extract_holiday_themes(query)
            entities['budgets'] = self._extract_holiday_budgets(query)
            # For holidays, "nights" can also be called "days"
            if not entities['nights']:
                entities['nights'] = self._extract_holiday_duration(query)
            # For holidays, extract guests (similar to hotels)
            entities['guests'] = self._extract_hotel_guests(query)
        
        return entities
    
    def _extract_cities(self, query: str) -> List[str]:
        """Extract city names from query using CityService."""
        found_cities = []
        query_lower = query.lower()
        
        # Use CityService cities for matching
        cities = self.city_service.get_all_cities()
        if not cities:
            # Fallback to self.cities if CityService is empty
            cities = self.cities
        
        for city in cities:
            city_lower = city.lower()
            # Check for exact word match
            pattern = r'\b' + re.escape(city_lower) + r'\b'
            if self.pattern_matcher.match_pattern(query_lower, pattern):
                found_cities.append(city)
                # Use CityService to validate city exists
                if not self.city_service.is_city_in_list(city):
                    # If city not in service, still include it (might be from fallback)
                    pass

        # Check alias matches (e.g., NYC -> New York)
        for alias, canonical in self.city_aliases.items():
            alias_pattern = r'\b' + re.escape(alias) + r'\b'
            if self.pattern_matcher.match_pattern(query_lower, alias_pattern):
                if canonical not in found_cities:
                    found_cities.append(canonical)

        # Check station code aliases (e.g., NDLS -> Delhi)
        for alias, canonical in self.station_aliases.items():
            alias_pattern = r'\b' + re.escape(alias) + r'\b'
            if self.pattern_matcher.match_pattern(query_lower, alias_pattern):
                if canonical not in found_cities:
                    found_cities.append(canonical)
        
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

    def _extract_date_ranges(self, query: str) -> List[Dict[str, str]]:
        """Extract date ranges or flexibility expressions."""
        ranges = []
        query_lower = query.lower()
        
        for pattern, range_type in self.DATE_RANGE_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                ranges.append({
                    'text': match.group(0),
                    'type': range_type,
                    'raw': match.group(0)
                })
        
        return ranges
    
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

    def _extract_time_preferences(self, query: str) -> List[Dict[str, str]]:
        """Extract time preference expressions."""
        prefs = []
        query_lower = query.lower()
        
        for pattern, pref_type in self.TIME_PREFERENCE_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                prefs.append({
                    'text': match.group(0),
                    'type': pref_type,
                    'raw': match.group(0)
                })
        
        return prefs
    
    def _extract_classes(self, query: str) -> List[str]:
        """Extract class types from query."""
        classes = []
        query_lower = query.lower()
        
        for pattern, class_type in self.CLASS_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                classes.append(class_type)
        
        return classes

    def _extract_price_constraints(self, query: str) -> List[Dict[str, str]]:
        """Extract price constraints and sort preferences."""
        prices = []
        query_lower = query.lower()
        
        for pattern, price_type in self.PRICE_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                prices.append({
                    'text': match.group(0),
                    'type': price_type,
                    'raw': match.group(0)
                })
        
        return prices

    def _extract_passengers(self, query: str) -> List[Dict[str, str]]:
        """Extract passenger count or group hints."""
        passengers = []
        query_lower = query.lower()
        
        for pattern, pax_type in self.PASSENGER_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                passengers.append({
                    'text': match.group(0),
                    'type': pax_type,
                    'raw': match.group(0)
                })
        
        # Also detect "for [number]" pattern as passengers if no nights mentioned
        # This helps with flexible ordering like "weekend for 2"
        if not passengers:
            # Check for "for [number]" that's not "for [number] nights"
            for_match = re.search(r'\bfor\s+(\d+)(?:\s+(passengers?|travelers?|people|adults?))?\b', query_lower)
            if for_match and 'night' not in query_lower:
                passengers.append({
                    'text': for_match.group(0),
                    'type': 'passengers',
                    'raw': for_match.group(0)
                })
        
        return passengers

    def _extract_stops(self, query: str) -> List[Dict[str, str]]:
        """Extract stop/layover preferences."""
        stops = []
        query_lower = query.lower()
        
        for pattern, stop_type in self.STOP_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                stops.append({
                    'text': match.group(0),
                    'type': stop_type,
                    'raw': match.group(0)
                })
        
        return stops

    def _extract_baggage(self, query: str) -> List[Dict[str, str]]:
        """Extract baggage preferences."""
        baggage = []
        query_lower = query.lower()
        
        for pattern, bag_type in self.BAGGAGE_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                baggage.append({
                    'text': match.group(0),
                    'type': bag_type,
                    'raw': match.group(0)
                })
        
        return baggage

    def _extract_trip_type(self, query: str) -> List[str]:
        """Extract trip type (one-way/round-trip/multi-city)."""
        types = []
        query_lower = query.lower()
        
        for pattern, trip_type in self.TRIP_TYPE_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                types.append(trip_type)
        
        return types

    def _extract_actions(self, query: str) -> List[Dict[str, str]]:
        """Extract booking actions or info requests."""
        actions = []
        query_lower = query.lower()
        
        for pattern, action_type in self.ACTION_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                actions.append({
                    'text': match.group(0),
                    'type': action_type,
                    'raw': match.group(0)
                })
        
        return actions

    def _extract_airline_preferences(self, query: str) -> List[Dict[str, str]]:
        """Extract airline preference or avoid hints."""
        prefs = []
        query_lower = query.lower()
        
        for pattern, pref_type in self.AIRLINE_PREFERENCE_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                prefs.append({
                    'text': match.group(0),
                    'type': pref_type,
                    'raw': match.group(0)
                })
        
        return prefs

    def _extract_loyalty(self, query: str) -> List[Dict[str, str]]:
        """Extract loyalty/miles preferences."""
        loyalty = []
        query_lower = query.lower()
        
        for pattern, loyalty_type in self.LOYALTY_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                loyalty.append({
                    'text': match.group(0),
                    'type': loyalty_type,
                    'raw': match.group(0)
                })
        
        return loyalty

    def _extract_special_needs(self, query: str) -> List[Dict[str, str]]:
        """Extract special assistance needs."""
        needs = []
        query_lower = query.lower()
        
        for pattern, need_type in self.SPECIAL_NEEDS_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                needs.append({
                    'text': match.group(0),
                    'type': need_type,
                    'raw': match.group(0)
                })
        
        return needs

    def _extract_station_codes(self, query: str) -> List[str]:
        """Extract station codes from query based on alias map."""
        found = []
        query_lower = query.lower()
        
        for code in self.station_aliases.keys():
            pattern = r'\b' + re.escape(code) + r'\b'
            if self.pattern_matcher.match_pattern(query_lower, pattern):
                found.append(code.upper())
        
        return found

    def _extract_berths(self, query: str) -> List[Dict[str, str]]:
        """Extract berth/seat preferences."""
        berths = []
        query_lower = query.lower()
        
        for pattern, berth_type in self.BERTH_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                berths.append({
                    'text': match.group(0),
                    'type': berth_type,
                    'raw': match.group(0)
                })
        
        return berths

    def _extract_quota(self, query: str) -> List[Dict[str, str]]:
        """Extract quota preferences."""
        quotas = []
        query_lower = query.lower()
        
        for pattern, quota_type in self.QUOTA_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                quotas.append({
                    'text': match.group(0),
                    'type': quota_type,
                    'raw': match.group(0)
                })
        
        return quotas

    def _extract_availability(self, query: str) -> List[Dict[str, str]]:
        """Extract availability/status queries."""
        availability = []
        query_lower = query.lower()
        
        for pattern, availability_type in self.AVAILABILITY_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                availability.append({
                    'text': match.group(0),
                    'type': availability_type,
                    'raw': match.group(0)
                })
        
        return availability

    def _extract_train_names(self, query: str) -> List[Dict[str, str]]:
        """Extract train name preferences."""
        names = []
        query_lower = query.lower()
        
        for pattern, name_type in self.TRAIN_NAME_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                names.append({
                    'text': match.group(0),
                    'type': name_type,
                    'raw': match.group(0)
                })
        
        return names

    def _extract_pnr(self, query: str) -> List[Dict[str, str]]:
        """Extract PNR/status related queries."""
        pnr = []
        query_lower = query.lower()
        
        for pattern, pnr_type in self.PNR_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                pnr.append({
                    'text': match.group(0),
                    'type': pnr_type,
                    'raw': match.group(0)
                })
        
        return pnr

    def _extract_hotel_nights(self, query: str) -> List[Dict[str, str]]:
        """Extract hotel stay nights."""
        nights = []
        query_lower = query.lower()
        
        for pattern, nights_type in self.HOTEL_NIGHTS_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                nights.append({
                    'text': match.group(0),
                    'type': nights_type,
                    'raw': match.group(0)
                })
        
        return nights

    def _extract_hotel_guests(self, query: str) -> List[Dict[str, str]]:
        """Extract hotel guest counts."""
        guests = []
        query_lower = query.lower()
        
        for pattern, guest_type in self.HOTEL_GUESTS_PATTERNS:
            # Skip "for [number]" pattern - it's ambiguous and should be treated as nights first
            # Only extract guests if explicitly mentioned (e.g., "for 3 guests", "with 3 guests")
            if guest_type == 'guests_for_number':
                continue
            # Also skip if "nights" or "days" appears (it's nights, not guests)
            if 'night' in query_lower or 'day' in query_lower:
                if re.search(r'\bfor\s+\d+\s+(nights?|days?)\b', query_lower):
                    continue
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                guests.append({
                    'text': match.group(0),
                    'type': guest_type,
                    'raw': match.group(0)
                })
        
        return guests

    def _extract_hotel_room_types(self, query: str) -> List[Dict[str, str]]:
        """Extract hotel room types."""
        room_types = []
        query_lower = query.lower()
        
        for pattern, room_type in self.HOTEL_ROOM_TYPE_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                room_types.append({
                    'text': match.group(0),
                    'type': room_type,
                    'raw': match.group(0)
                })
        
        return room_types

    def _extract_hotel_categories(self, query: str) -> List[Dict[str, str]]:
        """Extract hotel category/class."""
        categories = []
        query_lower = query.lower()
        
        for pattern, category_type in self.HOTEL_CATEGORY_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                categories.append({
                    'text': match.group(0),
                    'type': category_type,
                    'raw': match.group(0)
                })
        
        return categories
    
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

    def _extract_return_dates(self, query: str) -> List[Dict[str, str]]:
        """Extract return dates separately from departure dates."""
        return_dates = []
        query_lower = query.lower()
        
        for pattern, date_type in self.RETURN_DATE_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                return_dates.append({
                    'text': match.group(0),
                    'type': date_type,
                    'raw': match.group(0)
                })
        
        return return_dates
    
    def _extract_nights(self, query: str) -> List[Dict[str, str]]:
        """Extract number of nights for hotel stays."""
        nights = []
        query_lower = query.lower()
        
        for pattern, night_type in self.NIGHTS_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                nights.append({
                    'text': match.group(0),
                    'type': night_type,
                    'raw': match.group(0)
                })
        
        return nights
    
    def _extract_category(self, query: str) -> List[Dict[str, str]]:
        """Extract property class/category for hotels."""
        categories = []
        query_lower = query.lower()
        
        for pattern, cat_type in self.CATEGORY_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                categories.append({
                    'text': match.group(0),
                    'type': cat_type,
                    'raw': match.group(0)
                })
        
        return categories
    
    def _extract_holiday_themes(self, query: str) -> List[Dict[str, str]]:
        """Extract holiday theme preferences."""
        themes = []
        query_lower = query.lower()
        
        for pattern, theme_type in self.HOLIDAY_THEME_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                themes.append({
                    'text': match.group(0),
                    'type': theme_type,
                    'raw': match.group(0)
                })
        
        return themes
    
    def _extract_holiday_budgets(self, query: str) -> List[Dict[str, str]]:
        """Extract holiday budget preferences."""
        budgets = []
        query_lower = query.lower()
        
        for pattern, budget_type in self.HOLIDAY_BUDGET_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                budgets.append({
                    'text': match.group(0),
                    'type': budget_type,
                    'raw': match.group(0)
                })
        
        return budgets
    
    def _extract_holiday_duration(self, query: str) -> List[Dict[str, str]]:
        """Extract holiday duration (days/nights)."""
        durations = []
        query_lower = query.lower()
        
        for pattern, duration_type in self.HOLIDAY_DURATION_PATTERNS:
            match = self.pattern_matcher.match_pattern(query_lower, pattern)
            if match:
                durations.append({
                    'text': match.group(0),
                    'type': duration_type,
                    'raw': match.group(0)
                })
        
        return durations