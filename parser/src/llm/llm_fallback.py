"""LLM fallback service for when no rules match."""

from typing import List, Dict
from ..parser.rule_engine import RuleMatch
import dotenv
import os
import requests

dotenv.load_dotenv()

class LLMFallbackService:
    """Placeholder for LLM integration - called when no rules match."""
    
    def __init__(self):
        """Initialize LLM fallback service."""
        self.llm_client = None  # Will be initialized later
        self.enabled = False    # Feature flag
        self.url = os.getenv("LLM_FALLBACK_URL")
    
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
        return RuleMatch(
            intent=None,
            confidence=None,
            entities=None,
            next_slot=result["response"],
            match_text=result["latency_ms"]
        )
    
    
