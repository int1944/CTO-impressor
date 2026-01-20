import { useState, useRef, useEffect } from "react";

export function TravelInput({
  query,
  onQueryChange,
  onSuggestionSelect,
  onSubmit,
  cursorPosition,
  onCursorChange,
  placeholder = null,
  suggestions = [],
}) {
  const [localQuery, setLocalQuery] = useState(query);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Move cursor to end of input
  const moveCursorToEnd = () => {
    const input = inputRef.current;
    if (!input) return;
    const length = input.value.length;
    requestAnimationFrame(() => {
      input.setSelectionRange(length, length);
      input.scrollLeft = input.scrollWidth;
    });
  };

  useEffect(() => {
    // When query changes from outside (e.g., suggestion clicked), update and move cursor to end
    if (query !== localQuery) {
      setLocalQuery(query);
      moveCursorToEnd();
    }
  }, [query, localQuery]);

  useEffect(() => {
    // Show suggestions whenever available (even if user typed slot keyword)
    if (suggestions && suggestions.length > 0) {
      setShowSuggestions(true);
      setSelectedIndex(-1);
    } else {
      setShowSuggestions(false);
    }
  }, [suggestions]);

  const handleInputChange = (e) => {
    const newQuery = e.target.value;
    const cursorPos = e.target.selectionStart;
    setLocalQuery(newQuery);
    onQueryChange(newQuery);

    // Update cursor position
    if (onCursorChange) {
      onCursorChange(cursorPos);
    }
  };

  const handleKeyDown = (e) => {
    // Tab to select first suggestion
    if (e.key === "Tab" && suggestions.length > 0) {
      e.preventDefault();
      const firstSuggestion = suggestions[0];
      if (firstSuggestion && onSuggestionSelect) {
        onSuggestionSelect(firstSuggestion);
        setShowSuggestions(false);
      }
    }

    // Arrow down - navigate suggestions
    if (e.key === "ArrowDown" && showSuggestions && suggestions.length > 0) {
      e.preventDefault();
      setSelectedIndex((prev) => 
        prev < suggestions.length - 1 ? prev + 1 : 0
      );
    }

    // Arrow up - navigate suggestions
    if (e.key === "ArrowUp" && showSuggestions && suggestions.length > 0) {
      e.preventDefault();
      setSelectedIndex((prev) => 
        prev > 0 ? prev - 1 : suggestions.length - 1
      );
    }

    // Enter - select highlighted suggestion or submit
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (showSuggestions && selectedIndex >= 0 && suggestions[selectedIndex]) {
        onSuggestionSelect(suggestions[selectedIndex]);
        setShowSuggestions(false);
        setSelectedIndex(-1);
      } else if (onSubmit) {
        onSubmit(localQuery);
      }
    }

    // Escape - close suggestions
    if (e.key === "Escape") {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }

    // Number keys (1-8) - select suggestion by number
    if (e.key >= "1" && e.key <= "8") {
      const index = parseInt(e.key) - 1;
      if (showSuggestions && suggestions[index]) {
        e.preventDefault();
        onSuggestionSelect(suggestions[index]);
        setShowSuggestions(false);
        setSelectedIndex(-1);
      }
    }
  };

  const handleSubmit = () => {
    if (onSubmit) {
      onSubmit(localQuery);
    }
  };

  const handleSuggestionClick = (suggestion, e) => {
    e.preventDefault();
    e.stopPropagation();
    if (onSuggestionSelect) {
      onSuggestionSelect(suggestion);
    }
    setShowSuggestions(false);
    setSelectedIndex(-1);
    // Return focus to input
    inputRef.current?.focus();
  };

  const shouldShowPlaceholder = () => {
    if (!placeholder) return false;
    const queryLower = localQuery.toLowerCase().trim();
    const placeholderLower = placeholder.toLowerCase().trim();
    if (!queryLower) return true;

    // Hide if placeholder already exists in query
    if (queryLower.includes(placeholderLower)) return false;

    const queryWords = queryLower.split(/\s+/);
    const lastWord = queryWords[queryWords.length - 1] || "";
    const slotKeywords = ["to", "from", "on", "at", "in", "with", "for", "check-in", "check-out"];
    if (slotKeywords.includes(lastWord)) {
      const placeholderFirst = placeholderLower.split(/\s+/)[0];
      return lastWord === placeholderFirst;
    }

    return true;
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      {/* Input field */}
      <div className="relative flex items-center gap-3">
        <div className="relative flex-1">
          {/* Ghost placeholder text (appears after the actual text) */}
          {shouldShowPlaceholder() && placeholder && (
            <div
              className="pointer-events-none absolute inset-y-0 left-0 right-0 px-6 py-5 text-lg font-medium overflow-hidden whitespace-nowrap"
              aria-hidden="true"
            >
              {/* Invisible spacer matching the actual query text */}
              <span className="opacity-0">{localQuery || ""}</span>
              {/* Visible placeholder text */}
              <span className="text-gray-400/90">
                {localQuery ? " " : ""}
                {placeholder}
              </span>
            </div>
          )}
          {/* Actual input with visible text */}
          <input
            ref={inputRef}
            type="text"
            value={localQuery}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onSelect={(e) => {
              if (onCursorChange) {
                onCursorChange(e.target.selectionStart);
              }
            }}
            onFocus={() => {
              if (suggestions.length > 0) setShowSuggestions(true);
            }}
            className="w-full px-6 py-5 text-lg bg-white rounded-2xl border-0 focus:outline-none focus:ring-4 focus:ring-red-400/50 shadow-2xl transition-all duration-200 text-gray-800 caret-red-600 placeholder:text-gray-400 font-medium"
            placeholder="Ask Myra..."
            style={{
              caretColor: "#dc2626",
              direction: "ltr",
              textAlign: "left",
              overflowX: "auto",
              whiteSpace: "nowrap",
              scrollbarWidth: "thin",
              scrollbarColor: "#ef4444 #f3f4f6",
            }}
          />
        </div>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          className="w-12 h-12 rounded-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white flex items-center justify-center transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105"
          aria-label="Submit"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div 
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden animate-fade-in"
        >
          <div className="max-h-64 overflow-y-auto">
            {suggestions.slice(0, 8).map((suggestion, index) => {
              const isSelected = index === selectedIndex;
              return (
                <button
                  key={index}
                  onClick={(e) => handleSuggestionClick(suggestion, e)}
                  className={`w-full px-5 py-3 text-left flex items-center justify-between transition-colors ${
                    isSelected 
                      ? 'bg-red-50 text-red-700' 
                      : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <span className="font-medium">{suggestion.text}</span>
                  <span className="text-xs text-gray-400 ml-2">{index + 1}</span>
                </button>
              );
            })}
          </div>
          <div className="px-5 py-2 bg-gray-50 border-t border-gray-100 text-xs text-gray-500 flex items-center justify-between">
            <span>Press Tab or 1-8 to select</span>
            <span className="text-gray-400">↑↓ to navigate</span>
          </div>
        </div>
      )}
    </div>
  );
}
