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
        'holiday': ['intent', 'to', 'date', 'nights', 'theme', 'budget'],
    }
    
    # Optional slots (suggested conditionally, not in strict order)
    OPTIONAL_SLOTS = {
        'flight': ['return', 'passengers'],
        'hotel': ['nights', 'category', 'room_type', 'guests', 'amenities'],
        'train': ['passengers', 'time'],
        'holiday': ['guests', 'theme', 'budget'],  # Guests, theme and budget are optional
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
        'guests': ['guests', 'guest', 'people', 'persons', 'with', 'companion', 'partner', 'family', 'friends'],
        'rooms': ['room', 'rooms'],
        'quota': ['quota', 'tatkal', 'general'],
        'return': ['return', 'returning', 'coming back', 'round trip', 'round-trip'],
        'passengers': ['passengers', 'passenger', 'travelers', 'traveler', 'people', 'adults', 'adult'],
        'nights': ['nights', 'night', 'days', 'day'],
        'category': ['star', 'stars', 'budget', 'luxury', 'deluxe', 'premium', 'category', 'rating'],
        'room_type': ['single room', 'double room', 'suite', 'deluxe room'],
        'theme': ['theme', 'honeymoon', 'adventure', 'beach', 'family', 'mountains', 'romantic', 'cultural', 'religious'],
        'budget': ['budget', 'luxury', 'affordable', 'under', 'within', 'price', 'cost'],
        'amenities': ['with', 'amenities', 'amenity', 'facilities', 'facility', 'features', 'feature'],
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
        query_lower = query.lower().strip()

        # === HOTEL GUARDRAIL: check-in + check-out = no nights needed ===
        if intent == 'hotel':
            has_checkin = bool(re.search(r'\bcheck[-\s]?in\b', query_lower))
            has_checkout = bool(re.search(r'\bcheck[-\s]?out\b', query_lower))
            has_nights = bool(re.search(r'\b\d+\s*nights?\b', query_lower))
            
            # Rule 1: check-in + check-out → nights is filled
            if has_checkin and has_checkout:
                filled_slots.add('nights')
            
            # Rule 2: check-in + nights → checkout is filled
            if has_checkin and has_nights:
                filled_slots.add('checkout')

        # Special handling for incomplete "with" keyword (check VERY early, before other slot checks)
        # This must happen before checking for other slots to prioritize amenities
        # For hotels: "hotel with" -> amenities (priority), "hotel for 2 guests with" -> amenities (if guests filled)
        # For holidays: "holiday with" -> guests
        # For flights/trains: "flight with" -> passengers
        if query_lower.endswith(' with') or query_lower.endswith('with'):
            if intent == 'hotel':
                # Priority 1: If guests is already filled, "with" means amenities
                if 'guests' in filled_slots:
                    if 'amenities' not in filled_slots:
                        return 'amenities'
                # Priority 2: If "hotel" appears before "with" and no guests context, suggest amenities
                # This handles "hotel with" -> amenities
                elif re.search(r'\bhotel\b', query_lower) and not re.search(r'\b(for|with)\s+\d+\s+(guests?|people)\b', query_lower):
                    if 'amenities' not in filled_slots:
                        return 'amenities'
                # Priority 3: If there's a number before "with" that might be guests, suggest guests
                elif re.search(r'\b(for|with)\s+\d+\b', query_lower) and 'guests' not in filled_slots:
                    return 'guests'
                # Priority 4: Default to amenities if not filled
                elif 'amenities' not in filled_slots:
                    return 'amenities'
                # Fallback: suggest guests if amenities already filled
                elif 'guests' not in filled_slots:
                    return 'guests'
            elif intent == 'holiday':
                if 'guests' not in filled_slots:
                    return 'guests'
            elif intent in ['flight', 'train']:
                if 'passengers' not in filled_slots:
                    return 'passengers'
        
        # If user explicitly typed a slot keyword last, honor it (order-free)
        # BUT only if that slot is not already filled
        explicit_slot = self._get_last_keyword_slot(query, intent, filled_slots)
        if explicit_slot and explicit_slot not in filled_slots:
            return explicit_slot
        
        # Special handling for incomplete "for" keyword
        # "flight for" -> suggest passengers (for flights/trains)
        # "hotel for" -> suggest nights or guests (for hotels)
        if query_lower.endswith(' for') or query_lower.endswith('for'):
            if intent in ['flight', 'train']:
                if 'passengers' not in filled_slots:
                    return 'passengers'
            elif intent == 'hotel':
                # For hotels, "for" typically means nights first, then guests
                # Check if nights is already filled, if not suggest nights first
                if 'nights' not in filled_slots:
                    return 'nights'
                elif 'guests' not in filled_slots:
                    return 'guests'
                # If both are filled, check rooms
                elif 'rooms' not in filled_slots:
                    return 'rooms'
            elif intent == 'holiday':
                # For holidays, "for" could be nights or guests
                if 'nights' not in filled_slots:
                    return 'nights'
                elif 'guests' not in filled_slots:
                    return 'guests'
        
        # Flexible ordering: Check for any explicitly mentioned but unfilled slots first
        # This allows users to mention slots in any order
        
        # Check for explicitly mentioned slots that aren't filled yet
        # Priority: slots mentioned later in query (user is actively typing them)
        for slot in reversed(slot_order):  # Check in reverse order (later slots first)
            if slot in filled_slots:
                continue
            # Check if this slot's keyword appears in the query
            if self._has_slot_keyword(query_lower, slot):
                # If keyword exists but slot isn't filled, suggest this slot
                return slot
        
        # Also check optional slots that are explicitly mentioned
        optional_slots = self.OPTIONAL_SLOTS.get(intent, [])
        for slot in reversed(optional_slots):  # Check in reverse order
            if slot in filled_slots:
                continue
            if self._has_slot_keyword(query_lower, slot):
                # If keyword exists but slot isn't filled, suggest this slot
                return slot
        
        # For flights and trains, prioritize "from" and "to" before "date"
        # But allow flexibility - if user provides date, we can accept it
        if intent in ['flight', 'train']:
            # Check if "from" is not filled
            if 'from' not in filled_slots:
                return 'from'
            # Check if "to" is not filled
            if 'to' not in filled_slots:
                return 'to'
        
        # For holidays, prioritize "to" before "date", but allow flexible ordering
        if intent == 'holiday':
            # Check if "to" is not filled
            if 'to' not in filled_slots:
                return 'to'
        
        # Find first unfilled core slot
        # Special handling for hotels: skip checkout if nights is filled (checkout can be calculated)
        for slot in slot_order:
            if slot not in filled_slots:
                # For hotels, skip checkout if nights is filled
                if intent == 'hotel' and slot == 'checkout' and 'nights' in filled_slots:
                    continue
                return slot
        
        # All core slots filled, check optional slots conditionally
        optional_slots = self.OPTIONAL_SLOTS.get(intent, [])
        for slot in optional_slots:
            if slot not in filled_slots:
                # Check if this optional slot should be suggested
                if self._should_suggest_optional_slot(slot, query, intent, entities, filled_slots):
                    return slot
        
        # For hotels, if core slots (city, checkin, nights, guests) are filled, suggest room_type or category
        if intent == 'hotel':
            core_hotel_slots = ['city', 'checkin', 'nights', 'guests']
            if all(slot in filled_slots for slot in core_hotel_slots):
                # Suggest room_type first, then category
                if 'room_type' not in filled_slots and self._should_suggest_optional_slot('room_type', query, intent, entities, filled_slots):
                    return 'room_type'
                if 'category' not in filled_slots and self._should_suggest_optional_slot('category', query, intent, entities, filled_slots):
                    return 'category'
        
        return None  # All slots filled

    def _get_last_keyword_slot(self, query: str, intent: str, filled_slots: Set[str]) -> Optional[str]:
        """Return the slot whose keyword appears last in the query."""
        query_lower = query.lower()
        last_slot = None
        last_index = -1
        
        # Consider both core and optional slots relevant for this intent
        valid_slots = set(self.SLOT_ORDER.get(intent, [])).union(self.OPTIONAL_SLOTS.get(intent, []))
        
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
        
        # Check for intent (only filled if intent is actually detected, not None)
        if intent:
            filled_slots.add('intent')
        
        # Check for 'from' slot - only for flights, trains, and holidays (not hotels)
        # Only mark as filled if there's a city after "from"
        if intent in ['flight', 'train', 'holiday']:
            if self._has_slot_keyword(query_lower, 'from'):
                if self._slot_has_city_after_keyword(query_lower, entities.get('cities', []), 'from'):
                    filled_slots.add('from')
        
        # Check for 'to' slot - only mark as filled if there's a city after "to"
        # For hotels, "to" is not a valid slot (they use "city" instead)
        if intent != 'hotel':
            if self._has_slot_keyword(query_lower, 'to'):
                if self._slot_has_city_after_keyword(query_lower, entities.get('cities', []), 'to'):
                    filled_slots.add('to')
        elif intent == 'hotel':
            # For hotels, "to" is not used - they use "city" with "in" keyword
            pass
        
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
            # First city before "to" should be "from" (only for flights/trains/holidays)
            if intent in ['flight', 'train', 'holiday']:
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
            # Only for flights/trains/holidays (hotels use "city" with "in" keyword)
            if intent != 'hotel':
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
            # Only for flights/trains/holidays (hotels don't use "from")
            if intent in ['flight', 'train', 'holiday']:
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
            
            # Case 4: No keywords, but cities exist - assume first is "from" (for flights/trains/holidays only)
            # For hotels, cities are handled separately with "in" keyword
            if intent in ['flight', 'train', 'holiday']:
                if 'from' not in filled_slots and from_keyword_pos == -1 and to_keyword_pos == -1:
                    # No keywords at all, first city is likely "from"
                    if len(city_positions) >= 1:
                        filled_slots.add('from')
            elif intent == 'hotel':
                # For hotels, don't assume "from" - cities are handled with "in" keyword
                pass
        
        # Check for date slot
        if entities.get('dates'):
            filled_slots.add('date')
        
        # Check for time slot (only for flights and trains, not hotels)
        if entities.get('times') and intent in ['flight', 'train']:
            filled_slots.add('time')
        
        # Check for class slot
        if entities.get('classes'):
            filled_slots.add('class')
        
        # Check for passengers slot (flights, trains, and holidays)
        # Check both entity extraction and keyword patterns
        if intent in ['flight', 'train', 'holiday']:
            if entities.get('passengers'):
                filled_slots.add('passengers')
            # Also check for "for [number]" pattern that indicates passengers
            # BUT only if there's actually a number - "for" alone doesn't count
            elif self._has_passengers_pattern(query_lower):
                # Make sure it's not just "for" - need a number or explicit passengers word
                if re.search(r'\bfor\s+\d+\s+(passengers?|travelers?|people|adults?)\b', query_lower) or \
                   re.search(r'\b\d+\s+(passengers?|travelers?|people|adults?)\b', query_lower) or \
                   re.search(r'\bfor\s+\d+\b', query_lower):
                    filled_slots.add('passengers')
        
        # Check for nights slot (hotels and holidays)
        # Check both entity extraction and keyword patterns
        if intent in ['hotel', 'holiday']:
            if entities.get('nights'):
                filled_slots.add('nights')
            # Also check for "for [number] nights/days" pattern
            # BUT only if there's actually a number - "for" alone doesn't count
            elif self._has_nights_pattern(query_lower, intent):
                # Make sure it's not just "for" - need a number
                if re.search(r'\bfor\s+\d+\s+(nights?|days?)\b', query_lower) or re.search(r'\b\d+\s+(nights?|days?)\b', query_lower):
                    filled_slots.add('nights')
        
        # Intent-specific slots
        if intent == 'flight':
            if entities.get('airlines'):
                filled_slots.add('airline')
            # Check for return date slot - only mark as filled if there's actually a return date entity
            # If just the keyword "return" is mentioned, it should be the next slot to fill
            if entities.get('return_dates'):
                filled_slots.add('return')
        elif intent == 'hotel':
            # City slot for hotels - check if city is mentioned with "in" keyword
            if self._has_slot_keyword(query_lower, 'city') or entities.get('cities'):
                # Only mark city as filled if there's a city entity AND it appears after "in" keyword
                if entities.get('cities'):
                    # Check if city appears after "in" keyword
                    if self._slot_has_city_after_keyword(query_lower, entities.get('cities', []), 'in'):
                        filled_slots.add('city')
            # For hotels, if there's a date and no explicit checkin/checkout, treat it as checkin
            if self._has_slot_keyword(query_lower, 'checkin') or entities.get('checkin'):
                filled_slots.add('checkin')
            elif entities.get('dates') and 'checkin' not in filled_slots and not self._has_slot_keyword(query_lower, 'checkout'):
                # If there's a date and no explicit checkout, it's likely checkin
                filled_slots.add('checkin')
            if self._has_slot_keyword(query_lower, 'checkout') or entities.get('checkout'):
                filled_slots.add('checkout')
            # Check for guests - but prioritize nights if "for [number]" is ambiguous
            # "for 3" without "nights" or "guests" should be treated as nights first
            has_explicit_guests = self._has_slot_keyword(query_lower, 'guests') or \
                                 re.search(r'\bfor\s+\d+\s+guests?\b', query_lower) or \
                                 re.search(r'\bwith\s+\d+\s+guests?\b', query_lower) or \
                                 re.search(r'\b\d+\s+guests?\b', query_lower)
            
            if entities.get('guests'):
                # Only mark guests as filled if explicitly mentioned (not ambiguous "for [number]")
                if has_explicit_guests or not re.search(r'\bfor\s+\d+\b', query_lower):
                    filled_slots.add('guests')
            elif has_explicit_guests:
                filled_slots.add('guests')
            if self._has_slot_keyword(query_lower, 'rooms'):
                filled_slots.add('rooms')
            # Check for nights slot
            # Only mark as filled if there's actually a number, not just "for"
            if entities.get('nights'):
                filled_slots.add('nights')
            elif self._has_nights_pattern(query_lower, intent):
                filled_slots.add('nights')
            # Check for category slot
            if entities.get('hotel_categories') or self._has_slot_keyword(query_lower, 'category'):
                filled_slots.add('category')
            # Check for room type slot
            if entities.get('room_types') or self._has_slot_keyword(query_lower, 'room_type'):
                filled_slots.add('room_type')
            # Check for amenities slot - only mark as filled if there's an actual amenity entity
            # Don't mark as filled just because "with" keyword appears (it might be incomplete)
            if entities.get('amenities') and len(entities.get('amenities', [])) > 0:
                filled_slots.add('amenities')
            
            # === Hotel mutual exclusion rules ===
            # Detect check-in/check-out more robustly (handles "check-in", "checkin", "check in")
            has_checkin_keyword = bool(re.search(r'\bcheck[-\s]?in\b', query_lower))
            has_checkout_keyword = bool(re.search(r'\bcheck[-\s]?out\b', query_lower))
            has_nights_value = 'nights' in filled_slots or bool(re.search(r'\b\d+\s*nights?\b', query_lower))
            
            # Rule 1: If check-in + check-out are present → don't ask for nights
            if has_checkin_keyword and has_checkout_keyword:
                filled_slots.add('checkin')
                filled_slots.add('checkout')
                filled_slots.add('nights')  # Nights is implicitly known
            
            # Rule 2: If check-in + nights are present → don't ask for check-out
            if has_checkin_keyword and has_nights_value:
                filled_slots.add('checkin')
                filled_slots.add('nights')
                filled_slots.add('checkout')  # Checkout is implicitly known
                
        elif intent == 'train':
            if self._has_slot_keyword(query_lower, 'quota'):
                filled_slots.add('quota')
        elif intent == 'holiday':
            # Check for 'to' slot - mark as filled if there's a destination after "to"
            # Either a city entity OR just text after "to" keyword
            if self._has_slot_keyword(query_lower, 'to'):
                # Check if there's a city entity after "to"
                if self._slot_has_city_after_keyword(query_lower, entities.get('cities', []), 'to'):
                    filled_slots.add('to')
                # Also check if there's any word after "to" (like "to Maldives", "to Goa")
                elif re.search(r'\bto\s+[A-Za-z]+\b', query_lower):
                    filled_slots.add('to')
            # Check for guests slot - only mark as filled if there's an actual number
            # "with" alone should NOT mark guests as filled
            has_explicit_guests = re.search(r'\bfor\s+\d+\s+guests?\b', query_lower) or \
                                 re.search(r'\bwith\s+\d+\s+(guests?|people|persons?|friends?|family)?\b', query_lower) or \
                                 re.search(r'\b\d+\s+guests?\b', query_lower) or \
                                 re.search(r'\bwith\s+(my\s+)?(partner|spouse|wife|husband|family|friends)\b', query_lower)
            if entities.get('guests'):
                filled_slots.add('guests')
            elif has_explicit_guests:
                filled_slots.add('guests')
            # Check for theme slot - only mark as filled if theme has an actual value
            # "romantic" in "romantic getaway" is the theme
            if entities.get('themes'):
                filled_slots.add('theme')
            elif re.search(r'\b(honeymoon|adventure|beach|family|romantic|cultural|religious|wellness|spa)\s+(trip|getaway|vacation|holiday|retreat|escape)\b', query_lower):
                filled_slots.add('theme')
            # Check for budget slot
            if entities.get('budgets') or self._has_slot_keyword(query_lower, 'budget'):
                filled_slots.add('budget')
        
        return filled_slots

    def _has_for_number_guests(self, query_lower: str) -> bool:
        """Detect 'for <number>' guest patterns without nights."""
        if re.search(r'\bfor\s+\d+\s+nights?\b', query_lower):
            return False
        return re.search(r'\bfor\s+\d+\b', query_lower) is not None
    
    def _has_passengers_pattern(self, query_lower: str) -> bool:
        """Detect passengers patterns in query."""
        passenger_patterns = [
            r'\bfor\s+\d+\s+(passengers?|travelers?|people|adults?)\b',
            r'\b\d+\s+(passengers?|travelers?|people|adults?)\b',
            r'\bfor\s+\d+\b',  # "for 2" could be passengers if no nights mentioned
        ]
        for pattern in passenger_patterns:
            if self.pattern_matcher.match_pattern(query_lower, pattern):
                # Make sure it's not nights
                if not re.search(r'\bfor\s+\d+\s+nights?\b', query_lower):
                    return True
        return False
    
    def _has_nights_pattern(self, query_lower: str, intent: str) -> bool:
        """Detect nights/days patterns in query."""
        if intent not in ['hotel', 'holiday']:
            return False
        # Must have a number - "for" alone doesn't count
        nights_patterns = [
            r'\bfor\s+\d+\s+nights?\b',
            r'\bfor\s+\d+\s+days?\b',
            r'\b\d+\s+nights?\b',
            r'\b\d+\s+days?\b',
        ]
        for pattern in nights_patterns:
            if self.pattern_matcher.match_pattern(query_lower, pattern):
                return True
        return False

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
        
        # Guests slot: suggest if explicitly mentioned or if keyword detected (for holidays and hotels)
        if slot == 'guests':
            # Check if guests keyword is explicitly mentioned
            if self._has_slot_keyword(query_lower, 'guests'):
                return True
            # Check for "for [number] guests/people" pattern
            guest_patterns = [
                r'\bfor\s+\d+\s+guests?\b',
                r'\bwith\s+\d+\s+guests?\b',
                r'\b\d+\s+guests?\b',
            ]
            for pattern in guest_patterns:
                if self.pattern_matcher.match_pattern(query_lower, pattern):
                    return True
            # Don't suggest guests unless explicitly mentioned
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
            # For hotels, can suggest category after core slots (city, checkin, nights, guests) are filled
            if intent == 'hotel':
                core_slots_filled = 'city' in filled_slots and 'checkin' in filled_slots
                return core_slots_filled
            # Can suggest category after core slots are filled
            return True
        
        # Room type slot: suggest if keyword detected, otherwise after core slots
        if slot == 'room_type':
            # Check if room type keyword is mentioned
            if self._has_slot_keyword(query_lower, 'room_type'):
                return True
            # For hotels, can suggest room_type after core slots (city, checkin, nights, guests) are filled
            if intent == 'hotel':
                core_slots_filled = 'city' in filled_slots and 'checkin' in filled_slots
                return core_slots_filled
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
        
        # Amenities slot for hotels: suggest if keyword detected or after core slots
        if slot == 'amenities' and intent == 'hotel':
            # Check if amenities keyword is mentioned
            if self._has_slot_keyword(query_lower, 'amenities'):
                return True
            # Can suggest amenities after core slots (city, checkin) are filled
            if 'city' in filled_slots and 'checkin' in filled_slots:
                return True
            return False
        
        # Default: suggest if keyword detected
        return self._has_slot_keyword(query_lower, slot)