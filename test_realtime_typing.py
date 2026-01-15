"""Real-time typing with suggestions as you type (character by character)."""

import sys
import termios
import tty
from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator

class RealTimeTyper:
    """Real-time typing interface with live suggestions."""
    
    def __init__(self):
        self.engine = RuleEngine(enable_cache=True)
        self.generator = SuggestionGenerator()
        self.query = ""
        self.suggestions = []
        self.intent = None
        self.next_slot = None
    
    def get_char(self):
        """Get a single character from stdin without waiting for Enter."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    def update_suggestions(self):
        """Update suggestions based on current query."""
        match = self.engine.match(self.query)
        
        if match:
            self.intent = match.intent
            self.next_slot = match.next_slot
            if match.next_slot:
                suggestions = self.generator.generate(match, max_suggestions=8)
                self.suggestions = [s.text for s in suggestions]
            else:
                self.suggestions = []
        else:
            # Check for partial match
            match = self.engine._match_partial_intent(self.query)
            if match and match.next_slot == 'intent':
                self.intent = None
                self.next_slot = 'intent'
                self.suggestions = ['flight', 'hotel', 'train']
            else:
                self.intent = None
                self.next_slot = None
                self.suggestions = ['flight', 'hotel', 'train']  # Default fallback
    
    def display(self):
        """Display current state."""
        # Clear screen and move cursor to top
        print("\033[2J\033[H", end="")
        
        print("=" * 70)
        print("REAL-TIME TYPING WITH SUGGESTIONS")
        print("=" * 70)
        print("\nType your query (suggestions update as you type)")
        print("Press Tab to select suggestion, Backspace to delete, Ctrl+C to exit")
        print("=" * 70)
        
        print(f"\n📝 Query: {self.query}")
        print(f"   Cursor: {len(self.query)}")
        
        if self.intent:
            print(f"   Intent: {self.intent.upper()}")
        if self.next_slot:
            print(f"   Next Slot: {self.next_slot}")
        
        if self.suggestions:
            print(f"\n💡 Suggestions:")
            for i, s in enumerate(self.suggestions[:8], 1):
                marker = " ←" if i == 1 else ""
                print(f"   {i}. {s}{marker}")
        else:
            print("\n   (no suggestions)")
        
        print("\n" + "=" * 70)
        print(f"> {self.query}", end="", flush=True)
    
    def run(self):
        """Run the real-time typing interface."""
        self.display()
        
        try:
            while True:
                char = self.get_char()
                
                # Handle special characters
                if ord(char) == 3:  # Ctrl+C
                    print("\n\nGoodbye!")
                    break
                elif ord(char) == 127 or ord(char) == 8:  # Backspace
                    if len(self.query) > 0:
                        self.query = self.query[:-1]
                        self.update_suggestions()
                        self.display()
                elif ord(char) == 9:  # Tab - select first suggestion
                    if self.suggestions:
                        selected = self.suggestions[0]
                        self.query += " " + selected
                        self.update_suggestions()
                        self.display()
                elif ord(char) == 13 or ord(char) == 10:  # Enter
                    print(f"\n\n✓ Final query: '{self.query}'")
                    print("\nPress any key to continue, Ctrl+C to exit...")
                    self.get_char()
                    self.query = ""
                    self.update_suggestions()
                    self.display()
                elif char.isprintable():
                    # Regular character
                    self.query += char
                    self.update_suggestions()
                    self.display()
                    
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
        except Exception as e:
            print(f"\n\nError: {e}")

def main():
    """Main entry point."""
    try:
        typer = RealTimeTyper()
        typer.run()
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Real-time typing requires a terminal. Try 'python test_typing.py' for interactive mode.")

if __name__ == "__main__":
    main()
