"""Real-time typing with suggestions as you type (character by character)."""

import sys
import termios
import tty
from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator
from src.services.city_service import get_city_service

class RealTimeTyper:
    """Real-time typing interface with live suggestions."""
    
    def __init__(self):
        self.engine = RuleEngine(enable_cache=True)
        self.generator = SuggestionGenerator()
        self.query = ""
        self.suggestions = []
        self.placeholder = None
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
                suggestions = self.generator.generate(match, max_suggestions=8, include_placeholder=True, query=self.query)
                # Separate placeholder from entity suggestions
                self.suggestions = []
                self.placeholder = None
                for s in suggestions:
                    if s.is_placeholder:
                        self.placeholder = s.text
                    else:
                        self.suggestions.append(s.text)
            else:
                self.suggestions = []
                self.placeholder = None
        else:
            # Check for partial match
            match = self.engine._match_partial_intent(self.query)
            if match and match.next_slot == 'intent':
                self.intent = None
                self.next_slot = 'intent'
                self.suggestions = ['flight', 'hotel', 'train']
                self.placeholder = None
            else:
                self.intent = None
                self.next_slot = None
                self.suggestions = ['flight', 'hotel', 'train']  # Default fallback
                self.placeholder = None
    
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
        
        print(f"\n📝 Query: {self.query}", end="", flush=True)
        
        # Display ghost text (placeholder) in gray/dim
        if self.placeholder:
            query_lower = self.query.lower().strip()
            placeholder_lower = self.placeholder.lower().strip()
            query_words = query_lower.split()
            last_word = query_words[-1] if query_words else ""
            
            # Don't show placeholder if user has moved past it
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
                print(f"\033[2m {self.placeholder}\033[0m", end="", flush=True)
    
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
    
    def _is_prefix_word(self, word: str, selected_suggestion: str, query_words: list = None) -> tuple[bool, int]:
        """
        Check if a word (or multi-word phrase) is a city prefix that should be removed.
        
        Args:
            word: The word to check (usually last word of query)
            selected_suggestion: The selected suggestion text
            query_words: Optional list of all query words for multi-word prefix detection
            
        Returns:
            Tuple of (should_remove: bool, num_words: int) where num_words is 1 or 2
        """
        if not word:
            return (False, 0)
        
        word_lower = word.lower()
        suggestion_lower = selected_suggestion.lower()
        city_service = get_city_service()
        
        # Keywords to never remove (slot keywords)
        keywords = {'from', 'to', 'on', 'at', 'in', 'with', 'for', 'check-in', 'check-out', 'and', 'or'}
        if word_lower in keywords:
            return (False, 0)
        
        # If word is a complete city, don't remove it
        if city_service.is_city_in_list(word):
            return (False, 0)
        
        # If word matches the selected suggestion exactly, it's complete (don't remove)
        if word_lower == suggestion_lower:
            return (False, 0)
        
        # Try multi-word prefix detection if query_words is provided and last word is short
        if query_words and len(query_words) >= 2 and len(word_lower) <= 3:
            previous_word = query_words[-2]
            previous_word_lower = previous_word.lower()
            
            # Validate previous word for multi-word prefix
            if (previous_word_lower not in keywords and 
                not city_service.is_city_in_list(previous_word)):
                # Check if previous word appears at the start of any city name
                cities_with_previous = city_service.search_cities(prefix=previous_word_lower, limit=1)
                if cities_with_previous:
                    # Try multi-word prefix
                    multi_word_prefix = f"{previous_word_lower} {word_lower}"
                    matching_cities = city_service.search_cities(prefix=multi_word_prefix, limit=1)
                    if matching_cities:
                        # Check if the multi-word prefix matches the selected suggestion
                        if suggestion_lower.startswith(multi_word_prefix):
                            # It's a valid multi-word prefix - should remove 2 words
                            return (True, 2)
        
        # Fall back to single-word prefix check
        if suggestion_lower.startswith(word_lower):
            # Check if there are cities that start with this prefix
            matching_cities = city_service.search_cities(prefix=word_lower, limit=1)
            if matching_cities:
                # It's a valid prefix - should be removed (1 word)
                return (True, 1)
        
        return (False, 0)

    def _format_suggestion_with_placeholder(self, suggestion_text: str, placeholder_text: str) -> str:
        """Prefix suggestion with a slot keyword when the user hasn't typed it yet."""
        if not placeholder_text:
            return suggestion_text
        
        placeholder_first = placeholder_text.strip().split()[0].lower()
        prefix_candidates = {'from', 'to', 'on', 'at', 'in', 'with', 'for', 'check-in', 'check-out'}
        if placeholder_first not in prefix_candidates:
            return suggestion_text
        
        query_lower = self.query.lower().strip()
        last_word = query_lower.split()[-1] if query_lower else ""
        # If user already typed a different slot keyword, don't force the placeholder keyword
        if last_word in prefix_candidates and last_word != placeholder_first:
            return suggestion_text
        # Check if query already ends with the placeholder keyword (with or without trailing space)
        if last_word == placeholder_first or query_lower.rstrip().endswith(placeholder_first):
            return suggestion_text
        
        return f"{placeholder_first} {suggestion_text}"
        
        print(f"\n   Cursor: {len(self.query)}")
        
        if self.intent:
            print(f"   Intent: {self.intent.upper()}")
        if self.next_slot:
            print(f"   Next Slot: {self.next_slot}")
        
        if self.placeholder:
            print(f"\n💡 Placeholder (ghost text): \033[2m{self.placeholder}\033[0m")
        
        if self.suggestions:
            print(f"\n💡 Clickable Suggestions ({len(self.suggestions)}):")
            for i, s in enumerate(self.suggestions[:8], 1):
                marker = " ←" if i == 1 else ""
                print(f"   {i}. {s}{marker}")
        elif not self.placeholder:
            print("\n   (no suggestions)")
        
        print("\n" + "=" * 70)
        print(f"> {self.query}", end="", flush=True)
        
        # Show ghost text after cursor in input line too
        if self.placeholder:
            query_lower = self.query.lower().strip()
            placeholder_lower = self.placeholder.lower().strip()
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
            
            if should_show:
                print(f"\033[2m {self.placeholder}\033[0m", end="", flush=True)
    
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
                        
                        # Strip query to handle trailing spaces properly
                        self.query = self.query.strip()
                        
                        # Check if last word(s) is a prefix that should be removed
                        query_words = self.query.split()
                        last_word = query_words[-1] if query_words else ""
                        
                        # Check for prefix (single or multi-word)
                        should_remove, num_words = self._is_prefix_word(
                            last_word,
                            selected,
                            query_words
                        )
                        
                        # Remove prefix if detected (remove last N words)
                        if should_remove and num_words > 0:
                            self.query = " ".join(query_words[:-num_words])
                        
                        insert_text = self._format_suggestion_with_placeholder(selected, self.placeholder)
                        # Add space only if query is not empty
                        if self.query:
                            self.query += " " + insert_text
                        else:
                            self.query = insert_text
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
