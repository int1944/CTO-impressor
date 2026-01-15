"""Interactive test script for manual testing with custom queries."""

from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator

def test_query(query: str):
    """Test a single query and display results."""
    engine = RuleEngine(enable_cache=False)
    generator = SuggestionGenerator()
    
    print("\n" + "=" * 70)
    print(f"Query: '{query}'")
    print("=" * 70)
    
    match = engine.match(query)
    
    if match:
        if match.intent:
            print(f"\n✓ Intent Detected: {match.intent.upper()}")
        else:
            print(f"\n✓ Partial Match Detected (intent not yet specified)")
        print(f"  Confidence: {match.confidence:.2%}")
        print(f"  Next Slot: {match.next_slot}")
        
        if match.entities:
            print(f"\n  Extracted Entities:")
            for entity_type, values in match.entities.items():
                if values:
                    print(f"    - {entity_type}: {values}")
        
        suggestions = generator.generate(match, max_suggestions=10)
        if suggestions:
            print(f"\n  Suggestions ({len(suggestions)}):")
            for i, s in enumerate(suggestions, 1):
                print(f"    {i}. '{s.text}' (type: {s.entity_type}, confidence: {s.confidence:.2%})")
        else:
            print("\n  (no suggestions)")
    else:
        print("\n✗ No rule matched - would fallback to LLM")
        print("  (LLM fallback is currently disabled)")
    
    print("=" * 70)

def interactive_mode():
    """Run in interactive mode."""
    engine = RuleEngine(enable_cache=False)
    generator = SuggestionGenerator()
    
    print("\n" + "=" * 70)
    print("Interactive Query Tester")
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
            
            test_query(query)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific query from command line
        query = " ".join(sys.argv[1:])
        test_query(query)
    else:
        # Interactive mode
        interactive_mode()
