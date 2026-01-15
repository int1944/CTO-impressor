"""Slot inference module that determines next slot to fill."""

from typing import Optional, Dict
from .rules.slot_rules import SlotRules


class SlotInferencer:
    """Determines what entity slot should be filled next."""
    
    def __init__(self):
        """Initialize slot inferencer."""
        self.slot_rules = SlotRules()
    
    def infer(self, query: str, intent: str, entities: Dict) -> Optional[str]:
        """
        Infer the next slot to fill.
        
        Args:
            query: Current query text
            intent: Detected intent
            entities: Extracted entities
            
        Returns:
            Next slot name or None
        """
        return self.slot_rules.infer(query, intent, entities)
