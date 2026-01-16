"""Tests for slot inferencer."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.slot_inferencer import SlotInferencer


class TestSlotInferencer:
    """Test cases for SlotInferencer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.inferencer = SlotInferencer()
    
    def test_infer_from_slot(self):
        """Test inference of 'from' slot."""
        query = "I want to book a flight"
        entities = {'cities': []}
        next_slot = self.inferencer.infer(query, "flight", entities)
        
        assert next_slot == "from"
    
    def test_infer_to_slot(self):
        """Test inference of 'to' slot."""
        query = "Flight from Mumbai"
        entities = {'cities': ['Mumbai']}
        next_slot = self.inferencer.infer(query, "flight", entities)
        
        assert next_slot == "to"
    
    def test_infer_date_slot(self):
        """Test inference of 'date' slot."""
        query = "Flight from Mumbai to Delhi"
        entities = {'cities': ['Mumbai', 'Delhi']}
        next_slot = self.inferencer.infer(query, "flight", entities)
        
        assert next_slot == "date"
    
    def test_hotel_city_slot(self):
        """Test inference of hotel city slot."""
        query = "Book hotel"
        entities = {'cities': []}
        next_slot = self.inferencer.infer(query, "hotel", entities)
        
        assert next_slot == "city"
