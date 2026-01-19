"""LLM fallback service for when no rules match."""

from typing import List, Dict
from ..parser.rule_engine import RuleMatch
from ..parser.rules.entity_rules import EntityRules
import dotenv
import os
import requests
import time

dotenv.load_dotenv()

class LLMFallbackService:
    """Placeholder for LLM integration - called when no rules match."""
    
    def __init__(self):
        """Initialize LLM fallback service."""
        self.llm_client = None  # Will be initialized later
        self.enabled = False    # Feature flag
        self.url = os.getenv("LLM_FALLBACK_URL")
        self.entity_rules = EntityRules()  # Initialize entity rules for extraction
    
    async def get_next_slot(self, query: str) -> RuleMatch:
        """
        Get suggestions from LLM when no rules match.
        
        Args:
            query: User query text
                
        Returns:
            RuleMatch object
        """

        response = requests.post(self.url, json={"question": query})
        result = response.json()
        
        # Extract entities from the query (same as rule engine does)
        entities = self.entity_rules.extract(query, intent=None)
        
        
        return RuleMatch(
            intent=None,
            confidence=0.5,
            entities=entities,
            next_slot=result["response"],
            match_text=result["latency_ms"]
        )
    
    
