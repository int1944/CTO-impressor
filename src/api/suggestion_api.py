"""FastAPI endpoint for suggestion service."""

import time
from typing import List, Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from ..parser.rule_engine import RuleEngine
from ..parser.suggestion_generator import SuggestionGenerator
from ..llm.llm_fallback import LLMFallbackService
from ..utils.text_processor import TextProcessor


app = FastAPI(title="Suggestion API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize components
text_processor = TextProcessor()
# Disable cache to ensure fresh results (can re-enable in production for performance)
rule_engine = RuleEngine(enable_cache=False)
# Clear any existing cache on startup
if rule_engine.cache:
    rule_engine.cache.clear()
suggestion_generator = SuggestionGenerator()
llm_fallback = LLMFallbackService()


class SuggestionRequest(BaseModel):
    """Request model for suggestion endpoint."""
    query: str
    cursor_position: Optional[int] = None
    context: Optional[Dict] = None


class SuggestionResponse(BaseModel):
    """Response model for suggestion endpoint."""
    suggestions: List[Dict]
    intent: Optional[str] = None
    next_slot: Optional[str] = None
    source: str
    latency_ms: float


@app.post("/suggest", response_model=SuggestionResponse)
async def get_suggestions(request: SuggestionRequest):
    """
    Real-time suggestion endpoint.
    Called as user types (with debouncing on client side).
    
    Args:
        request: Suggestion request with query and context
        
    Returns:
        Suggestion response with suggestions and metadata
    """
    start_time = time.time()
    
    # For empty queries, return intent suggestions
    if not request.query or not request.query.strip():
        # Create a partial match to suggest intents
        from ..parser.rule_engine import RuleMatch
        partial_match = RuleMatch(
            intent=None,
            confidence=0.5,
            entities={},
            next_slot='intent',
            match_text=None
        )
        suggestions = suggestion_generator.generate(partial_match, include_placeholder=True, query=request.query)
        suggestions_dict = [s.to_dict() for s in suggestions]
        
        return SuggestionResponse(
            suggestions=suggestions_dict,
            intent=None,
            next_slot='intent',
            source="empty_query",
            latency_ms=round((time.time() - start_time) * 1000, 2)
        )
    
    # Preprocess query
    processed_query = text_processor.normalize(request.query)
    
    # Try rule-based parsing first
    rule_match = rule_engine.match(processed_query, request.context or {})
    
    if rule_match:
        # Generate suggestions from rules (include placeholder and pass query for prefix detection)
        source = "rule_based"
        intent = rule_match.intent
        next_slot = rule_match.next_slot
        latency_ms = (time.time() - start_time) * 1000

    else:
        # Fallback to LLM
        rule_match = await llm_fallback.get_next_slot(processed_query)
        source = "llm_fallback"
        intent = None
        next_slot = rule_match.next_slot
        latency_ms = rule_match.match_text
    
    suggestions = suggestion_generator.generate(rule_match, include_placeholder=True, query=request.query)
    # Convert suggestions to dict

    suggestions_dict = [s.to_dict() for s in suggestions]
    
    
    return SuggestionResponse(
        suggestions=suggestions_dict,
        intent=intent,
        next_slot=next_slot,
        source=source,
        latency_ms=round(latency_ms, 2)
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/clear-cache")
async def clear_cache():
    """Clear the rule engine cache."""
    if rule_engine.cache:
        rule_engine.cache.clear()
    return {"status": "cache_cleared", "message": "Rule engine cache cleared successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
