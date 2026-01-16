"""Real-time typing simulator to test suggestions as you type."""

import sys
import time
from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator

def get_suggestions(query: str):
    """Get suggestions for a query."""
    engine = RuleEngine(enable_cache=True)  # Use cache for better performance
    generator = SuggestionGenerator()
    
    match = engine.match(query)
    
    if match:
        suggestions = generator.generate(match, max_suggestions=8)
        return {
            'intent': match.intent,
            'next_slot': match.next_slot,
            'suggestions': [s.text for s in suggestions],
            'source': 'rule_based'
        }
    else:
        return {
            'intent': None,
            'next_slot': None,
            'suggestions': ['flight', 'hotel', 'train'],  # Generic fallback
            'source': 'llm_fallback'
        }

def display_suggestions(query: str, result: dict):
    """Display suggestions in a nice format."""
    # Clear screen (works on most terminals)
    print("\033[2J\033[H", end="")
    
    print("=" * 70)
    print("REAL-TIME SUGGESTION TESTER")
    print("=" * 70)
    print(f"\nQuery: '{query}'")
    print(f"Intent: {result['intent'].upper() if result['intent'] else 'None'}")
    print(f"Next Slot: {result['next_slot'] or 'N/A'}")
    print(f"Source: {result['source']}")
    print("\n" + "-" * 70)
    print("SUGGESTIONS (tap number or type to continue):")
    print("-" * 70)
    
    if result['suggestions']:
        for i, suggestion in enumerate(result['suggestions'], 1):
            print(f"  [{i}] {suggestion}")
    else:
        print("  (no suggestions)")
    
    print("-" * 70)
    print("\nType your query (or number to select suggestion):")

def simulate_typing():
    """Simulate real-time typing with suggestions."""
    print("\033[2J\033[H", end="")  # Clear screen
    print("=" * 70)
    print("REAL-TIME SUGGESTION TESTER")
    print("=" * 70)
    print("\nType your query character by character.")
    print("Suggestions will update as you type.")
    print("Press Enter to finish, Ctrl+C to exit")
    print("=" * 70)
    
    query = ""
    
    try:
        while True:
            # Get current suggestions
            result = get_suggestions(query)
            display_suggestions(query, result)
            
            # Get next character
            char = sys.stdin.read(1)
            
            if char == '\n':  # Enter pressed
                if query.strip():
                    print(f"\n✓ Final query: '{query}'")
                    print("\nPress Enter to start new query, or Ctrl+C to exit")
                    sys.stdin.read(1)  # Wait for Enter
                    query = ""
                    continue
                else:
                    continue
            
            elif char == '\x7f' or char == '\b':  # Backspace
                if len(query) > 0:
                    query = query[:-1]
            elif ord(char) == 3:  # Ctrl+C
                print("\n\nGoodbye!")
                break
            else:
                query += char
            
    except KeyboardInterrupt:
        print("\n\nGoodbye!")

def interactive_mode():
    """Interactive mode where you type and see suggestions update."""
    print("\n" + "=" * 70)
    print("REAL-TIME SUGGESTION TESTER")
    print("=" * 70)
    print("\nType your query and see suggestions update in real-time.")
    print("Press Enter after each query to see suggestions.")
    print("Type 'quit' to exit.")
    print("=" * 70)
    
    query = ""
    
    while True:
        try:
            # Get input
            user_input = input(f"\n> {query}").strip()
            
            if not user_input:
                # Show suggestions for current query
                if query:
                    result = get_suggestions(query)
                    display_suggestions(query, result)
                    
                    # Show suggestions
                    print(f"\nSuggestions for: '{query}'")
                    if result['suggestions']:
                        for i, s in enumerate(result['suggestions'], 1):
                            print(f"  {i}. {s}")
                    else:
                        print("  (no suggestions)")
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            # Check if user selected a suggestion number
            if user_input.isdigit():
                num = int(user_input)
                result = get_suggestions(query)
                if 1 <= num <= len(result['suggestions']):
                    selected = result['suggestions'][num - 1]
                    query += " " + selected
                    print(f"✓ Added: '{selected}'")
                    continue
            
            # Append to query
            query += " " + user_input if query else user_input
            
            # Show updated suggestions
            result = get_suggestions(query)
            print(f"\nCurrent query: '{query}'")
            print(f"Intent: {result['intent'] or 'None'}")
            print(f"Next slot: {result['next_slot'] or 'N/A'}")
            if result['suggestions']:
                print("Suggestions:")
                for i, s in enumerate(result['suggestions'], 1):
                    print(f"  {i}. {s}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break

def step_by_step_demo():
    """Show how suggestions change as query progresses."""
    print("\n" + "=" * 70)
    print("STEP-BY-STEP DEMO: How suggestions change as you type")
    print("=" * 70)
    
    # Progressive queries
    queries = [
        "I",
        "I want",
        "I want to",
        "I want to book",
        "I want to book a",
        "I want to book a flight",
        "I want to book a flight from",
        "I want to book a flight from Mumbai",
        "I want to book a flight from Mumbai to",
    ]
    
    for query in queries:
        result = get_suggestions(query)
        print(f"\nQuery: '{query}'")
        print(f"  Intent: {result['intent'] or 'None'}")
        print(f"  Next Slot: {result['next_slot'] or 'N/A'}")
        if result['suggestions']:
            print(f"  Suggestions: {', '.join(result['suggestions'][:5])}")
        print("-" * 70)
        time.sleep(0.5)  # Small delay for demo effect

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            step_by_step_demo()
        elif sys.argv[1] == "interactive":
            interactive_mode()
        else:
            # Test specific query
            query = " ".join(sys.argv[1:])
            result = get_suggestions(query)
            display_suggestions(query, result)
    else:
        # Default: interactive mode
        interactive_mode()
