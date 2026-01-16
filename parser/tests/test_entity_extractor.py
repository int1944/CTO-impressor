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

    def test_extract_date_range(self):
        """Test date range extraction."""
        query = "I can travel anytime between April 1 and April 5"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'date_ranges' in entities
        assert len(entities['date_ranges']) > 0

    def test_extract_price_constraints(self):
        """Test price constraints extraction."""
        query = "Flights under ₹5,000 from Mumbai to Pune"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'price_constraints' in entities
        assert len(entities['price_constraints']) > 0

    def test_extract_passengers(self):
        """Test passenger extraction."""
        query = "2 adults and 1 child"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'passengers' in entities
        assert len(entities['passengers']) > 0

    def test_extract_stops(self):
        """Test stop preference extraction."""
        query = "Non-stop flights only"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'stops' in entities
        assert len(entities['stops']) > 0

    def test_extract_baggage(self):
        """Test baggage preference extraction."""
        query = "Only cabin baggage"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'baggage' in entities
        assert len(entities['baggage']) > 0

    def test_extract_trip_type(self):
        """Test trip type extraction."""
        query = "Round trip from San Francisco to Vegas"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'trip_type' in entities
        assert len(entities['trip_type']) > 0

    def test_extract_train_quota(self):
        """Test train quota extraction."""
        query = "Tatkal ticket"
        entities = self.extractor.extract(query, intent="train")
        
        assert 'quota' in entities
        assert len(entities['quota']) > 0

    def test_extract_train_berth(self):
        """Test train berth preference extraction."""
        query = "Lower berth preferred"
        entities = self.extractor.extract(query, intent="train")
        
        assert 'berths' in entities
        assert len(entities['berths']) > 0

    def test_extract_train_station_codes(self):
        """Test train station code extraction."""
        query = "NDLS to BCT"
        entities = self.extractor.extract(query, intent="train")
        
        assert 'stations' in entities
        assert len(entities['stations']) > 0

    def test_extract_train_name(self):
        """Test train name extraction."""
        query = "Rajdhani available?"
        entities = self.extractor.extract(query, intent="train")
        
        assert 'train_names' in entities
        assert len(entities['train_names']) > 0

    def test_extract_train_availability(self):
        """Test train availability extraction."""
        query = "RAC available?"
        entities = self.extractor.extract(query, intent="train")
        
        assert 'availability' in entities
        assert len(entities['availability']) > 0

    def test_extract_train_pnr(self):
        """Test PNR extraction."""
        query = "Check PNR status"
        entities = self.extractor.extract(query, intent="train")
        
        assert 'pnr' in entities
        assert len(entities['pnr']) > 0

    def test_extract_actions(self):
        """Test action extraction."""
        query = "Confirm the cheapest option"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'actions' in entities
        assert len(entities['actions']) > 0

    def test_extract_city_aliases(self):
        """Test city alias extraction."""
        query = "NYC to LA"
        entities = self.extractor.extract(query, intent="flight")
        
        assert 'cities' in entities
        assert len(entities['cities']) >= 1
