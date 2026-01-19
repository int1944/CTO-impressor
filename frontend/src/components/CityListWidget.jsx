import { useState, useMemo } from 'react';

export function CityListWidget({ suggestions, onCitySelect, entityType }) {
  const [searchTerm, setSearchTerm] = useState('');

  // Filter city suggestions
  const citySuggestions = useMemo(() => {
    return suggestions.filter(
      (s) => 
        !s.is_placeholder && 
        s.selectable && 
        (s.entity_type === 'to' || s.entity_type === 'from' || s.entity_type === 'city')
    );
  }, [suggestions]);

  // Filter by search term
  const filteredCities = useMemo(() => {
    if (!searchTerm) return citySuggestions;
    return citySuggestions.filter((city) =>
      city.text.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [citySuggestions, searchTerm]);

  if (citySuggestions.length === 0) {
    return null;
  }

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
      <div className="space-y-3">
        {/* Search input */}
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search cities..."
          className="w-full px-4 py-2 rounded-xl bg-white/60 border border-peach-200 focus:border-peach-400 focus:outline-none text-sm"
        />

        {/* City list */}
        <div className="max-h-64 overflow-y-auto space-y-2">
          {filteredCities.length === 0 ? (
            <div className="text-center text-gray-400 text-sm py-4">
              No cities found
            </div>
          ) : (
            filteredCities.map((city, index) => (
              <button
                key={`city-${index}`}
                onClick={() => onCitySelect && onCitySelect(city)}
                className="w-full text-left px-4 py-3 rounded-xl bg-white/60 hover:bg-white/80 transition-all duration-200 border border-peach-200 hover:border-peach-400 hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className="text-gray-800 font-medium">{city.text}</span>
                  {city.confidence && (
                    <span className="text-xs text-peach-600">
                      {Math.round(city.confidence * 100)}%
                    </span>
                  )}
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
