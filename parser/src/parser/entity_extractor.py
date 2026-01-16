"""Entity extraction module that uses entity rules."""

from typing import Dict, Optional
from .rules.entity_rules import EntityRules


class EntityExtractor:
    """Extracts entities from query text using entity rules."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize entity extractor.
        
        Args:
            data_dir: Directory containing entity data files
        """
        self.entity_rules = EntityRules(data_dir)
    
    def extract(self, query: str, intent: Optional[str] = None) -> Dict:
        """
        Extract entities from query.
        
        Args:
            query: Query text
            intent: Detected intent (optional, helps with context)
            
        Returns:
            Dict with extracted entities
        """
        return self.entity_rules.extract(query, intent)
