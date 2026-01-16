"""Integration tests for the suggestion system."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator


class TestIntegration:
    """Integration test cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RuleEngine(enable_cache=False)
        self.generator = SuggestionGenerator()
    
    def test_end_to_end_flight_query(self):
        """Test end-to-end flow for flight query."""
        query = "I want to book a flight"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "flight"
        
        suggestions = self.generator.generate(match)
        assert len(suggestions) > 0
        assert all(s.entity_type == match.next_slot for s in suggestions)
    
    def test_end_to_end_hotel_query(self):
        """Test end-to-end flow for hotel query."""
        query = "Book hotel in"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "hotel"
        
        suggestions = self.generator.generate(match)
        assert len(suggestions) > 0
    
    def test_end_to_end_train_query(self):
        """Test end-to-end flow for train query."""
        query = "I need a train"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "train"
        
        suggestions = self.generator.generate(match)
        assert len(suggestions) > 0
