"""City Search API Service - Filters cities by name prefix and ranks by population."""

import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import requests

app = FastAPI(title="City Search API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store cities data
cities_df = None
cities = None

class CitySuggestion(BaseModel):
    """Model for a city suggestion."""
    name: str
    population: int


class CitySearchResponse(BaseModel):
    """Response model for city search."""
    suggestions: List[CitySuggestion]
    count: int
    query: str

class CityInListRespone(BaseModel):
    """Response model for city belonging"""
    inList: bool


def load_cities_data():
    """Load cities data from CSV file."""
    global cities_df
    global cities
    csv_path = os.path.join(os.path.dirname(__file__), 'cities.csv')
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Cities CSV file not found at {csv_path}")
    
    cities_df = pd.read_csv(csv_path)
    
    # Ensure data types are correct
    cities_df['name'] = cities_df['name'].astype(str).str.strip()
    cities_df['population'] = pd.to_numeric(cities_df['population'], errors='coerce')
    
    # Remove any rows with missing data
    cities_df = cities_df.dropna(subset=['name', 'population'])
    
    print(f"Loaded {len(cities_df)} cities from {csv_path}")
    cities = set(cities_df["name"].str.lower().values)


@app.on_event("startup")
async def startup_event():
    """Load cities data when the application starts."""
    load_cities_data()


@app.get("/search", response_model=CitySearchResponse)
async def search_cities(
    q: str = Query(..., description="Search query (city name prefix)", min_length=1),
    limit: int = Query(10, description="Maximum number of results to return", ge=1, le=100)
):
    """
    Search for cities by name prefix (lexical matching).
    Results are ranked by population (highest first).
    
    Args:
        q: The search query (city name prefix)
        limit: Maximum number of results to return (default: 10, max: 100)
        
    Returns:
        CitySearchResponse with matching cities sorted by population
    """
    if cities_df is None:
        load_cities_data()
    
    # Normalize query: strip whitespace and convert to lowercase for case-insensitive matching
    query_normalized = q.strip().lower()
    
    if not query_normalized:
        return CitySearchResponse(
            suggestions=[],
            count=0,
            query=q
        )
    
    # Filter cities where name starts with the query (case-insensitive)
    # Using str.lower() for case-insensitive matching
    mask = cities_df['name'].str.lower().str.startswith(query_normalized)
    filtered_df = cities_df[mask].copy()
    
    # Already sorted by population descending, so just take the top results
    top_results = filtered_df.head(limit)
    
    # Convert to response format
    suggestions = [
        CitySuggestion(name=row['name'], population=int(row['population']))
        for _, row in top_results.iterrows()
    ]
    
    return CitySearchResponse(
        suggestions=suggestions,
        count=len(suggestions),
        query=q
    )

@app.get("/in-list")
async def city_in_list(
    q: str = Query(..., description="Search query (city name prefix)", min_length=1)
):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=1&language=en&format=json"
    response = requests.get(geo_url)
    data = response.json()
    if data["results"]:
        city = data["results"][0]["name"]
        print(city.lower())
        if city.lower() in cities:
            return CityInListRespone(inList=True)
        else:
            return CityInListRespone(inList=False)
    else:
        return CityInListRespone(inList=False)



@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "cities_loaded": len(cities_df) if cities_df is not None else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
