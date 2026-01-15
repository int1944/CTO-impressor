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
        print("\nType your query (ghost text shows what to type next)")
        print("Commands: Tab=select 1st suggestion, Backspace=delete, Enter=new query, Ctrl+C=exit")
        print("=" * 70)
        
        # Get match and suggestions
        match = self.engine.match(self.query)
        placeholder_text = None
        entity_suggestions = []  # Initialize to avoid undefined variable
        
        if match:
            if match.intent:
                print(f"\n✓ Intent: {match.intent.upper()}")
            else:
                print(f"\n⚠ Partial match (intent not specified)")
            print(f"   Next Slot: {match.next_slot}")
            
            suggestions = self.generator.generate(match, max_suggestions=8, include_placeholder=True) if match.next_slot else []
            
            # Extract placeholder text for ghost text display
            if suggestions and suggestions[0].is_placeholder:
                placeholder_text = suggestions[0].text
                entity_suggestions = suggestions[1:]  # Skip placeholder
            else:
                entity_suggestions = suggestions
        else:
            # Fallback for partial queries
            match = self.engine._match_partial_intent(self.query)
            if match and match.next_slot == 'intent':
                suggestions = [self.generator.Suggestion(text=s, entity_type='intent', confidence=0.5, selectable=True, is_placeholder=False) 
                             for s in ['flight', 'hotel', 'train']]
                entity_suggestions = suggestions
            else:
                entity_suggestions = []
        
        # Display query with ghost text
        print(f"\n📝 Query: ", end="", flush=True)
        print(f"{self.query}", end="", flush=True)
        
        # Display ghost text (placeholder) in gray/dim
        if placeholder_text:
            # Check if user has moved past this placeholder
            query_lower = self.query.lower().strip()
            placeholder_lower = placeholder_text.lower().strip()
            
            # Get the last few words to check if user is typing something different
            query_words = query_lower.split()
            last_word = query_words[-1] if query_words else ""
            
            # Don't show placeholder if:
            # 1. Placeholder is already in the query
            # 2. User has typed a word that suggests they're filling a different slot
            # 3. User is typing a city name (hide placeholder immediately)
            should_show = True
            if placeholder_lower in query_lower:
                should_show = False
            elif last_word in ['to', 'from', 'on', 'at', 'in', 'with', 'for']:
                # User is typing a preposition/slot keyword
                # Check if it matches the placeholder
                placeholder_words = placeholder_lower.split()
                placeholder_first_word = placeholder_words[0] if placeholder_words else ""
                
                if last_word == placeholder_first_word:
                    # User is typing the placeholder keyword, show it
                    should_show = True
                else:
                    # User typed a different keyword (e.g., "to" when placeholder is "from")
                    # Don't show old placeholder - it will update on next keystroke
                    should_show = False
            # Check if user is typing a city name - hide placeholder only if it's a partial match
            # (user actively typing), not if they've completed typing a city
            elif self._is_typing_city_partial(last_word):
                should_show = False
            # Also check if query ends with a space and a keyword that conflicts
            elif query_lower.endswith(' to ') or query_lower.endswith(' to'):
                if 'from' in placeholder_lower:
                    should_show = False
            elif query_lower.endswith(' from ') or query_lower.endswith(' from'):
                if 'to' in placeholder_lower and 'from' not in placeholder_lower:
                    should_show = False
            
            if should_show:
                # ANSI codes: \033[2m = dim, \033[90m = gray, \033[0m = reset
                print(f"\033[2m {placeholder_text}\033[0m", end="", flush=True)
        
        print()  # New line after query
        
        # Display entity suggestions (clickable)
        if entity_suggestions:
            print(f"\n💡 Clickable Suggestions ({len(entity_suggestions)}):")
            for i, s in enumerate(entity_suggestions, 1):
                marker = " ← Press Tab" if i == 1 and s.selectable else ""
                text = s.text if hasattr(s, 'text') else s
                print(f"   {i}. {text}{marker}")
        elif placeholder_text:
            print("\n   (type the placeholder above or select from suggestions)")
        else:
            print("\n   (no suggestions yet)")
        
        print("\n" + "=" * 70)
        print(f"> {self.query}", end="", flush=True)
        
        # Show ghost text after cursor in input line too
        if placeholder_text:
            query_lower = self.query.lower().strip()
            placeholder_lower = placeholder_text.lower().strip()
            query_words = query_lower.split()
            last_word = query_words[-1] if query_words else ""
            
            should_show = True
            if placeholder_lower in query_lower:
                should_show = False
            elif last_word in ['to', 'from', 'on', 'at', 'in', 'with', 'for']:
                placeholder_words = placeholder_lower.split()
                placeholder_first_word = placeholder_words[0] if placeholder_words else ""
                if last_word == placeholder_first_word:
                    should_show = True
                else:
                    should_show = False
            elif self._is_typing_city_partial(last_word):
                should_show = False
            elif query_lower.endswith(' to ') or query_lower.endswith(' to'):
                if 'from' in placeholder_lower:
                    should_show = False
            elif query_lower.endswith(' from ') or query_lower.endswith(' from'):
                if 'to' in placeholder_lower and 'from' not in placeholder_lower:
                    should_show = False
            
            if should_show:
                print(f"\033[2m {placeholder_text}\033[0m", end="", flush=True)
    
    def _is_typing_city(self, word: str) -> bool:
        """Check if the word matches or starts with a city name."""
        if not word:
            return False
        
        word_lower = word.lower()
        # Check against known cities
        cities = self.generator.cities
        for city in cities:
            city_lower = city.lower()
            # Check if word matches city or city starts with word (user typing city)
            if word_lower == city_lower or city_lower.startswith(word_lower):
                return True
        return False
    
    def _is_typing_city_partial(self, word: str) -> bool:
        """Check if user is actively typing a city (partial match, not complete)."""
        if not word:
            return False
        
        word_lower = word.lower()
        cities = self.generator.cities
        
        # Check if it's a partial match (city starts with word but word is shorter)
        for city in cities:
            city_lower = city.lower()
            # Only return True if it's a partial match (user still typing)
            # Not if it's a complete match (user finished typing)
            if city_lower.startswith(word_lower) and word_lower != city_lower:
                return True
        return False
    
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
                
                # Tab - select first selectable suggestion (skip placeholder)
                elif ord(char) == 9:
                    match = self.engine.match(self.query)
                    if match and match.next_slot:
                        suggestions = self.generator.generate(match, max_suggestions=8, include_placeholder=True)
                        # Find first selectable suggestion (skip placeholder)
                        selectable_suggestion = None
                        for s in suggestions:
                            if s.selectable and not s.is_placeholder:
                                selectable_suggestion = s
                                break
                        
                        if selectable_suggestion:
                            self.query += " " + selectable_suggestion.text
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
