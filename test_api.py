"""Test the API endpoint with custom queries."""

import requests
import json

API_URL = "http://localhost:8000/suggest"

def test_api_query(query: str, cursor_position: int = None):
    """Test a query via the API."""
    payload = {
        "query": query,
        "cursor_position": cursor_position,
        "context": {}
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        print("\n" + "=" * 70)
        print(f"Query: '{query}'")
        print("=" * 70)
        print(f"Source: {result['source']}")
        print(f"Latency: {result['latency_ms']}ms")
        
        if result.get('intent'):
            print(f"Intent: {result['intent'].upper()}")
        if result.get('next_slot'):
            print(f"Next Slot: {result['next_slot']}")
        
        print(f"\nSuggestions ({len(result['suggestions'])}):")
        for i, s in enumerate(result['suggestions'], 1):
            print(f"  {i}. '{s['text']}' (type: {s['entity_type']}, conf: {s['confidence']:.2%})")
        
        print("=" * 70)
        
        return result
        
    except requests.exceptions.ConnectionError:
        print(f"\nError: Could not connect to API at {API_URL}")
        print("Make sure the server is running:")
        print("  uvicorn src.api.suggestion_api:app --reload")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None

def interactive_api_mode():
    """Run in interactive mode with API."""
    print("\n" + "=" * 70)
    print("API Query Tester")
    print("=" * 70)
    print("Enter your queries (type 'quit' or 'exit' to stop)")
    print("=" * 70)
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            test_api_query(query)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        test_api_query(query)
    else:
        interactive_api_mode()
