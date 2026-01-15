"""LLM fallback service for when no rules match."""

from typing import List, Dict
from ..parser.suggestion_generator import Suggestion


class LLMFallbackService:
    """Placeholder for LLM integration - called when no rules match."""
    
    def __init__(self):
        """Initialize LLM fallback service."""
        self.llm_client = None  # Will be initialized later
        self.enabled = False    # Feature flag
    
    async def get_suggestions(self, query: str, context: Dict = None) -> List[Suggestion]:
        """
        Get suggestions from LLM when no rules match.
        
        Args:
            query: User query text
            context: Optional context dictionary
            
        Returns:
            List of suggestions
        """
        if context is None:
            context = {}
        
        if not self.enabled:
            # Return generic fallback suggestions
            return [
                Suggestion(text="flight", entity_type="intent", confidence=0.3),
                Suggestion(text="hotel", entity_type="intent", confidence=0.3),
                Suggestion(text="train", entity_type="intent", confidence=0.3),
            ]
        
        # Future: Call actual LLM API
        # response = await self.llm_client.complete(query, context)
        # return self._parse_llm_response(response)
        
        return []
    
    def _parse_llm_response(self, response: str) -> List[Suggestion]:
        """
        Parse LLM response into suggestions.
        
        This is a placeholder for future implementation.
        
        Args:
            response: LLM API response
            
        Returns:
            List of suggestions
        """
        # TODO: Implement LLM response parsing
        return []
