"""Live typing test - see suggestions update as you type (requires terminal)."""

import sys
import os

# Check if we're in a proper terminal
if not sys.stdin.isatty():
    print("Error: This script requires a terminal (not a pipe or redirect)")
    print("Usage: python test_live.py")
    sys.exit(1)

try:
    import termios
    import tty
except ImportError:
    print("Error: termios not available (Windows not supported)")
    print("Use 'python test_typing.py' for interactive mode instead")
    sys.exit(1)

from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator

class LiveTyper:
    """Live typing with real-time suggestions."""
    
    def __init__(self):
        self.engine = RuleEngine(enable_cache=True)
        self.generator = SuggestionGenerator()
        self.query = ""
    
    def get_char(self):
        """Get single character without Enter."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    def clear_and_display(self):
        """Clear screen and display current state."""
        os.system('clear' if os.name != 'nt' else 'cls')
        
        print("=" * 70)
        print("LIVE TYPING - Suggestions update as you type!")
        print("=" * 70)
        print("\nType your query (suggestions appear below)")
        print("Commands: Tab=select 1st suggestion, Backspace=delete, Enter=new query, Ctrl+C=exit")
        print("=" * 70)
        
        # Get match and suggestions
        match = self.engine.match(self.query)
        
        print(f"\n📝 Query: '{self.query}'")
        print(f"   Length: {len(self.query)} chars")
        
        if match:
            if match.intent:
                print(f"   ✓ Intent: {match.intent.upper()}")
            else:
                print(f"   ⚠ Partial match (intent not specified)")
            print(f"   Next Slot: {match.next_slot}")
            
            suggestions = self.generator.generate(match, max_suggestions=8) if match.next_slot else []
        else:
            # Fallback for partial queries
            match = self.engine._match_partial_intent(self.query)
            if match and match.next_slot == 'intent':
                suggestions = [self.generator.Suggestion(text=s, entity_type='intent', confidence=0.5) 
                             for s in ['flight', 'hotel', 'train']]
            else:
                suggestions = []
        
        if suggestions:
            print(f"\n💡 Suggestions ({len(suggestions)}):")
            for i, s in enumerate(suggestions, 1):
                marker = " ← Press Tab" if i == 1 else ""
                text = s.text if hasattr(s, 'text') else s
                print(f"   {i}. {text}{marker}")
        else:
            print("\n   (no suggestions yet)")
        
        print("\n" + "=" * 70)
        print(f"> {self.query}", end="", flush=True)
    
    def run(self):
        """Run live typing interface."""
        self.clear_and_display()
        
        try:
            while True:
                char = self.get_char()
                
                # Ctrl+C
                if ord(char) == 3:
                    print("\n\nGoodbye!")
                    break
                
                # Backspace
                elif ord(char) == 127 or ord(char) == 8:
                    if len(self.query) > 0:
                        self.query = self.query[:-1]
                        self.clear_and_display()
                
                # Tab - select first suggestion
                elif ord(char) == 9:
                    match = self.engine.match(self.query)
                    if match and match.next_slot:
                        suggestions = self.generator.generate(match, max_suggestions=1)
                        if suggestions:
                            self.query += " " + suggestions[0].text
                            self.clear_and_display()
                    else:
                        # Partial match - suggest intents
                        partial = self.engine._match_partial_intent(self.query)
                        if partial and partial.next_slot == 'intent':
                            self.query += " flight"  # Default to flight
                            self.clear_and_display()
                
                # Enter - new query
                elif ord(char) == 13 or ord(char) == 10:
                    print(f"\n\n✓ Query completed: '{self.query}'")
                    input("\nPress Enter to start new query...")
                    self.query = ""
                    self.clear_and_display()
                
                # Regular character
                elif char.isprintable():
                    self.query += char
                    self.clear_and_display()
                    
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
        except Exception as e:
            print(f"\n\nError: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    typer = LiveTyper()
    typer.run()
