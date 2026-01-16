"""Live typing test - see suggestions update as you type (requires terminal)."""

import sys
import os
import time
import asyncio

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
from src.services.city_service import get_city_service
from src.llm.llm_fallback import LLMFallbackService

class LiveTyper:
    """Live typing with real-time suggestions."""
    
    def __init__(self):
        self.engine = RuleEngine(enable_cache=True)
        self.generator = SuggestionGenerator()
        self.query = ""
        self.llm_fallback = LLMFallbackService()
    
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
        print("Commands: Tab=select 1st suggestion, 1-8=select suggestion, Backspace=delete, Enter=new query, Ctrl+C=exit")
        print("=" * 70)

        start_time = time.time()
        
        # Get match and suggestions
        match = self.engine.match(self.query)
        placeholder_text = None
        entity_suggestions = []  # Initialize to avoid undefined variable
        if match:
            print("match intent : ", match.intent)
            print("match next slot : ", match.next_slot)
        
        
        # Fallback to LLM if rule engine doesn't return anything (only when user enters space)
        if not match and self.query and len(self.query.strip()) > 0 and self.query.endswith(' '):
            try:
                match = asyncio.run(self.llm_fallback.get_next_slot(self.query))
                print("llm response")
                print("llm intent : ", match.intent)
                print("llm next slot : ", match.next_slot)
            except Exception as e:
                print(f"LLM fallback error: {e}")
                match = None
        
        suggestions = self.generator.generate(match, max_suggestions=8, include_placeholder=True, query=self.query) if match and match.next_slot else []
        
        if suggestions and suggestions[0].is_placeholder:
            placeholder_text = suggestions[0].text
            entity_suggestions = suggestions[1:]  # Skip placeholder
        else:
            entity_suggestions = suggestions

        print(f"Latency (test_live): {(time.time() - start_time) * 1000} ms")

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

    def _format_nights_selection(self, suggestion_text: str, placeholder_text: str) -> str:
        """Append 'night(s)' when selecting a number for nights."""
        if not placeholder_text or 'night' not in placeholder_text.lower():
            return suggestion_text
        
        if suggestion_text.isdigit():
            return f"{suggestion_text} night" if suggestion_text == "1" else f"{suggestion_text} nights"
        
        return suggestion_text
    
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
                
                # Number keys - select corresponding suggestion (1-8)
                elif char.isdigit() and char != '0':
                    match = self.engine.match(self.query)
                    if match and match.next_slot:
                        suggestions = self.generator.generate(match, max_suggestions=8, include_placeholder=True, query=self.query)
                        placeholder_text = suggestions[0].text if suggestions and suggestions[0].is_placeholder else None
                        entity_suggestions = [s for s in suggestions if s.selectable and not s.is_placeholder]
                        
                        index = int(char) - 1
                        if 0 <= index < len(entity_suggestions):
                            selectable_suggestion = entity_suggestions[index]
                            
                            # Strip query to handle trailing spaces properly
                            self.query = self.query.strip()
                            
                            # Check if last word(s) is a prefix that should be removed
                            query_words = self.query.split()
                            last_word = query_words[-1] if query_words else ""
                            
                            # Check for prefix (single or multi-word)
                            should_remove, num_words = self._is_prefix_word(
                                last_word, 
                                selectable_suggestion.text,
                                query_words
                            )
                            
                            # Remove prefix if detected (remove last N words)
                            if should_remove and num_words > 0:
                                self.query = " ".join(query_words[:-num_words])
                            
                            insert_text = self._format_suggestion_with_placeholder(
                                selectable_suggestion.text,
                                placeholder_text
                            )
                            insert_text = self._format_nights_selection(insert_text, placeholder_text)
                            # Add space only if query is not empty
                            if self.query:
                                self.query += " " + insert_text
                            else:
                                self.query = insert_text
                            self.clear_and_display()
                        else:
                            self.query += char
                            self.clear_and_display()
                    else:
                        self.query += char
                        self.clear_and_display()
                
                # Tab - select first selectable suggestion (skip placeholder)
                elif ord(char) == 9:
                    match = self.engine.match(self.query)
                    if match and match.next_slot:
                        suggestions = self.generator.generate(match, max_suggestions=8, include_placeholder=True, query=self.query)
                        # Find first selectable suggestion (skip placeholder)
                        selectable_suggestion = None
                        placeholder_text = None
                        if suggestions and suggestions[0].is_placeholder:
                            placeholder_text = suggestions[0].text
                        for s in suggestions:
                            if s.selectable and not s.is_placeholder:
                                selectable_suggestion = s
                                break
                        
                        if selectable_suggestion:
                            # Strip query to handle trailing spaces properly
                            self.query = self.query.strip()
                            
                            # Check if last word(s) is a prefix that should be removed
                            query_words = self.query.split()
                            last_word = query_words[-1] if query_words else ""
                            
                            # Check for prefix (single or multi-word)
                            should_remove, num_words = self._is_prefix_word(
                                last_word, 
                                selectable_suggestion.text,
                                query_words
                            )
                            
                            # Remove prefix if detected (remove last N words)
                            if should_remove and num_words > 0:
                                self.query = " ".join(query_words[:-num_words])
                            
                            insert_text = self._format_suggestion_with_placeholder(
                                selectable_suggestion.text,
                                placeholder_text
                            )
                            insert_text = self._format_nights_selection(insert_text, placeholder_text)
                            # Add space only if query is not empty
                            if self.query:
                                self.query += " " + insert_text
                            else:
                                self.query = insert_text
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
