"""City Service - CSV-based city operations with population ranking."""

import os
import pandas as pd
from typing import List, Optional
from pathlib import Path


class CityService:
    """Service for city operations using CSV data."""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize city service.
        
        Args:
            csv_path: Path to cities.csv file. If None, looks for cities.csv in project root.
        """
        self.csv_path = csv_path or self._find_csv_path()
        self.cities_df: Optional[pd.DataFrame] = None
        self.cities_set: Optional[set] = None
        self._load_cities()
    
    def _find_csv_path(self) -> str:
        """Find cities.csv file in project root."""
        # Try project root first
        project_root = Path(__file__).parent.parent.parent
        csv_path = project_root / 'cities.csv'
        if csv_path.exists():
            return str(csv_path)
        
        # Fallback to current directory
        return os.path.join(os.path.dirname(__file__), '..', '..', 'cities.csv')
    
    def _load_cities(self):
        """Load cities data from CSV file."""
        if not os.path.exists(self.csv_path):
            print(f"Warning: Cities CSV file not found at {self.csv_path}")
            print("Falling back to empty city list. City suggestions will be limited.")
            self.cities_df = pd.DataFrame(columns=['name', 'population'])
            self.cities_set = set()
            return
        
        try:
            self.cities_df = pd.read_csv(self.csv_path)
            
            # Ensure data types are correct
            self.cities_df['name'] = self.cities_df['name'].astype(str).str.strip()
            self.cities_df['population'] = pd.to_numeric(self.cities_df['population'], errors='coerce')
            
            # Remove any rows with missing data
            self.cities_df = self.cities_df.dropna(subset=['name', 'population'])
            
            # Sort by population descending for better suggestions
            self.cities_df = self.cities_df.sort_values('population', ascending=False).reset_index(drop=True)
            
            # Create set for fast lookup
            self.cities_set = set(self.cities_df['name'].str.lower().values)
            
            print(f"Loaded {len(self.cities_df)} cities from {self.csv_path}")
        except Exception as e:
            print(f"Error loading cities from CSV: {e}")
            print("Falling back to empty city list.")
            self.cities_df = pd.DataFrame(columns=['name', 'population'])
            self.cities_set = set()
    
    def search_cities(self, prefix: str = "", limit: int = 10, exclude: Optional[str] = None) -> List[str]:
        """
        Search for cities by name prefix (case-insensitive).
        Results are ranked by population (highest first).
        
        Args:
            prefix: City name prefix to search for. Empty string returns top cities.
            limit: Maximum number of results to return
            exclude: City name to exclude from results (e.g., exclude 'from' city when suggesting 'to')
            
        Returns:
            List of city names sorted by population
        """
        if self.cities_df is None or len(self.cities_df) == 0:
            return []
        
        # Normalize prefix
        prefix_normalized = prefix.strip().lower() if prefix else ""
        
        # Filter cities where name starts with the prefix (case-insensitive)
        if prefix_normalized:
            mask = self.cities_df['name'].str.lower().str.startswith(prefix_normalized)
            filtered_df = self.cities_df[mask].copy()
        else:
            # No prefix - return top cities by population
            filtered_df = self.cities_df.copy()
        
        # Exclude specific city if provided
        if exclude:
            exclude_lower = exclude.lower()
            filtered_df = filtered_df[filtered_df['name'].str.lower() != exclude_lower]
        
        # Already sorted by population descending, so just take the top results
        top_results = filtered_df.head(limit)
        
        # Return list of city names
        return top_results['name'].tolist()
    
    def is_city_in_list(self, city_name: str) -> bool:
        """
        Check if a city name exists in the city list (case-insensitive).
        
        Args:
            city_name: City name to check
            
        Returns:
            True if city exists, False otherwise
        """
        if not self.cities_set:
            return False
        
        return city_name.lower() in self.cities_set
    
    def get_all_cities(self) -> List[str]:
        """
        Get all city names (for backward compatibility).
        
        Returns:
            List of all city names sorted by population
        """
        if self.cities_df is None or len(self.cities_df) == 0:
            return []
        
        return self.cities_df['name'].tolist()


# Global instance (singleton pattern)
_city_service_instance: Optional[CityService] = None


def get_city_service() -> CityService:
    """Get or create the global CityService instance."""
    global _city_service_instance
    if _city_service_instance is None:
        _city_service_instance = CityService()
    return _city_service_instance
