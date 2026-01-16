"""Real-time typing test - type queries and see suggestions update."""

from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator

def get_suggestions_for_query(query: str):
    """Get suggestions for a query."""
    engine = RuleEngine(enable_cache=True)
    generator = SuggestionGenerator()
    
    match = engine.match(query)
    
    if match and match.next_slot:
        suggestions = generator.generate(match, max_suggestions=8)
        return {
            'intent': match.intent,
            'next_slot': match.next_slot,
            'suggestions': [s.text for s in suggestions],
            'source': 'rule_based'
        }
    else:
        # For partial queries, suggest intents
        if not match or (match and match.intent is None):
            return {
                'intent': None,
                'next_slot': 'intent',
                'suggestions': ['flight', 'hotel', 'train'],
                'source': 'partial_match'
            }
        return {
            'intent': match.intent if match else None,
            'next_slot': None,
            'suggestions': [],
            'source': 'no_match'
        }

def main():
    """Interactive typing test."""
    print("\n" + "=" * 70)
    print("REAL-TIME TYPING TESTER")
    print("=" * 70)
    print("\nType your query and see suggestions update in real-time!")
    print("Examples:")
    print("  - 'I want to book a' → suggests: flight, hotel, train")
    print("  - 'I want to book a flight' → suggests: cities (from)")
    print("  - 'Book hotel in' → suggests: cities")
    print("\nType 'quit' to exit")
    print("=" * 70)
    
    query = ""
    
    while True:
        try:
            # Show current state
            if query:
                result = get_suggestions_for_query(query)
                print(f"\n📝 Current query: '{query}'")
                if result['intent']:
                    print(f"   Intent: {result['intent'].upper()}")
                if result['next_slot']:
                    print(f"   Next slot: {result['next_slot']}")
                if result['suggestions']:
                    print(f"   💡 Suggestions:")
                    for i, s in enumerate(result['suggestions'], 1):
                        print(f"      {i}. {s}")
                print()
            
            # Get input
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            # Check if user selected a suggestion number
            if user_input.isdigit():
                if query:
                    result = get_suggestions_for_query(query)
                    num = int(user_input)
                    if 1 <= num <= len(result['suggestions']):
                        selected = result['suggestions'][num - 1]
                        query += " " + selected
                        print(f"✓ Added: '{selected}'")
                        continue
            
            # Append to query
            if query:
                query += " " + user_input
            else:
                query = user_input
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
