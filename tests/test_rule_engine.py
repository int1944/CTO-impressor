"""Tests for rule engine."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.rule_engine import RuleEngine


class TestRuleEngine:
    """Test cases for RuleEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RuleEngine(enable_cache=False)
    
    def test_flight_intent_detection(self):
        """Test flight intent detection."""
        query = "I want to book a flight"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "flight"
        assert match.confidence > 0.75
    
    def test_flight_round_trip_intent(self):
        """Test round-trip flight intent detection."""
        query = "Book a round-trip flight from Delhi to Mumbai"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "flight"

    def test_flight_budget_intent(self):
        """Test budget/cheapest flight intent detection."""
        query = "What's the cheapest flight from Delhi to Bangalore?"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "flight"
    
    def test_hotel_intent_detection(self):
        """Test hotel intent detection."""
        query = "Book hotel in Mumbai"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "hotel"
        assert match.confidence > 0.75
    
    def test_train_intent_detection(self):
        """Test train intent detection."""
        query = "I need a train ticket"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "train"
        assert match.confidence > 0.75

    def test_train_intent_basic_search(self):
        """Test train intent detection for basic search."""
        query = "Find trains from Delhi to Mumbai"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "train"

    def test_train_intent_station_codes(self):
        """Test train intent detection for station codes."""
        query = "NDLS to BCT"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.intent == "train"
    
    def test_no_intent_match(self):
        """Test query with no matching intent."""
        query = "What is the weather today"
        match = self.engine.match(query)
        
        assert match is None
    
    def test_entity_extraction(self):
        """Test entity extraction."""
        query = "Flight from Mumbai to Delhi"
        match = self.engine.match(query)
        
        assert match is not None
        assert len(match.entities.get('cities', [])) > 0
    
    def test_slot_inference(self):
        """Test slot inference."""
        query = "I want to book a flight"
        match = self.engine.match(query)
        
        assert match is not None
        assert match.next_slot is not None
        assert match.next_slot in ['from', 'to', 'date', 'time', 'class', 'airline']
