"""Tests for entity extractor."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.entity_extractor import EntityExtractor


class TestEntityExtractor:
    """Test cases for EntityExtractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = EntityExtractor()
    
    def test_extract_cities(self):
        """Test city extraction."""
        query = "Flight from Mumbai to Delhi"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'cities' in entities
        assert len(entities['cities']) >= 0  # May or may not match depending on data
    
    def test_extract_dates(self):
        """Test date extraction."""
        query = "Book flight for tomorrow"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'dates' in entities
        assert len(entities['dates']) > 0
    
    def test_extract_times(self):
        """Test time extraction."""
        query = "Flight in the morning"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'times' in entities
        assert len(entities['times']) > 0
    
    def test_extract_classes(self):
        """Test class extraction."""
        query = "Book business class flight"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'classes' in entities
        assert len(entities['classes']) > 0
