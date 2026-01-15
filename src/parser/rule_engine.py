"""Main rule engine that orchestrates rule matching."""

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
            return None
        
        # Check cache
        if self.cache:
            cached = self.cache.get(query)
            if cached:
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
        
        # No match found
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