export function SuggestionBox({ suggestions, onSuggestionClick, loading }) {
  if (loading) {
    return (
      <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
        <div className="flex items-center space-x-2 text-peach-600">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-peach-300 border-t-peach-600"></div>
          <span className="text-sm">Loading suggestions...</span>
        </div>
      </div>
    );
  }

  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  // Separate placeholders from selectable suggestions
  const placeholders = suggestions.filter(s => s.is_placeholder);
  const selectable = suggestions.filter(s => !s.is_placeholder && s.selectable);

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md animate-fade-in">
      {/* Placeholder suggestions (ghost text) */}
      {placeholders.length > 0 && (
        <div className="mb-3 pb-2 border-b border-peach-200">
          {placeholders.map((suggestion, index) => (
            <div
              key={`placeholder-${index}`}
              className="text-gray-400 text-sm italic mb-1 opacity-60"
            >
              {suggestion.text}
            </div>
          ))}
        </div>
      )}

      {/* Selectable suggestions */}
      {selectable.length > 0 && (
        <div className="space-y-2">
          {selectable.map((suggestion, index) => (
            <button
              key={`suggestion-${index}`}
              onClick={() => onSuggestionClick && onSuggestionClick(suggestion)}
              className="w-full text-left px-4 py-3 rounded-xl bg-white/60 hover:bg-white/90 transition-all duration-200 border border-peach-200 hover:border-peach-400 hover:shadow-md hover:scale-[1.02]"
            >
              <div className="flex items-center justify-between">
                <span className="text-gray-800 font-medium">
                  {suggestion.text}
                </span>
                {suggestion.entity_type && (
                  <span className="text-xs text-peach-600 bg-peach-100 px-2 py-1 rounded-full">
                    {suggestion.entity_type}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* "See more" indicator if there are many suggestions */}
      {selectable.length >= 8 && (
        <div className="mt-3 text-center">
          <span className="text-xs text-gray-400 italic">see more</span>
        </div>
      )}
    </div>
  );
}
