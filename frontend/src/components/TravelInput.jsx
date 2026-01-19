import { useState, useRef, useEffect } from 'react';

export function TravelInput({ 
  query, 
  onQueryChange, 
  onSuggestionSelect, 
  onSubmit,
  cursorPosition,
  onCursorChange 
}) {
  const [localQuery, setLocalQuery] = useState(query);
  const inputRef = useRef(null);

  useEffect(() => {
    setLocalQuery(query);
  }, [query]);

  const handleInputChange = (e) => {
    const newQuery = e.target.value;
    setLocalQuery(newQuery);
    onQueryChange(newQuery);
    
    // Update cursor position
    if (onCursorChange) {
      onCursorChange(e.target.selectionStart);
    }
  };

  const handleKeyDown = (e) => {
    // Tab to select first suggestion
    if (e.key === 'Tab' && onSuggestionSelect) {
      e.preventDefault();
      // This will be handled by parent component
    }
    
    // Enter to submit
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (onSubmit) {
        onSubmit(localQuery);
      }
    }
  };

  const handleSubmit = () => {
    if (onSubmit) {
      onSubmit(localQuery);
    }
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      {/* Input field with entity highlighting */}
      <div className="relative">
        {/* Actual input */}
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
          className="w-full px-6 py-4 text-lg bg-white/90 backdrop-blur-sm rounded-2xl border-2 border-peach-200 focus:border-peach-400 focus:outline-none glow-effect transition-all duration-200 text-gray-800 caret-peach-600 placeholder:text-gray-400"
          placeholder="Book a flight to..."
          style={{
            caretColor: '#f16a22',
          }}
        />

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-peach-500 hover:bg-peach-600 text-white flex items-center justify-center transition-all duration-200 shadow-lg hover:shadow-xl"
          aria-label="Submit"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
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
    </div>
  );
}
