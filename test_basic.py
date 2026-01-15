"""Basic test script to verify the system works."""

from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator

def test_basic():
    """Test basic functionality."""
    engine = RuleEngine(enable_cache=False)
    generator = SuggestionGenerator()
    
    # Test queries
    test_queries = [
        "I want to book a flight",
        "Book hotel in",
        "I need a train",
    ]
    
    print("Testing rule-based parser...")
    print("-" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        match = engine.match(query)
        
        if match:
            print(f"  Intent: {match.intent}")
            print(f"  Confidence: {match.confidence:.2f}")
            print(f"  Next Slot: {match.next_slot}")
            print(f"  Entities: {match.entities}")
            
            suggestions = generator.generate(match)
            print(f"  Suggestions ({len(suggestions)}):")
            for s in suggestions[:5]:
                print(f"    - {s.text} ({s.entity_type}, conf: {s.confidence:.2f})")
        else:
            print("  No match found")
    
    print("\n" + "-" * 50)
    print("Basic test completed!")

if __name__ == "__main__":
    test_basic()
