import { useMemo } from "react";

export function AirlineWidget({ suggestions, onAirlineSelect }) {
  // Filter airline suggestions
  const airlineSuggestions = useMemo(() => {
    return suggestions.filter(
      (s) =>
        !s.is_placeholder &&
        s.selectable &&
        s.entity_type === "airline"
    );
  }, [suggestions]);

  if (airlineSuggestions.length === 0) {
    return null;
  }

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Select airline
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {airlineSuggestions.map((airline, index) => (
            <button
              key={`airline-${index}`}
              onClick={() => onAirlineSelect && onAirlineSelect(airline)}
              className="flex items-center justify-center px-4 py-3 rounded-xl bg-white/60 hover:bg-white/80 transition-all duration-200 border border-peach-200 hover:border-peach-400 hover:shadow-md hover:scale-105"
            >
              <span className="text-sm font-medium text-gray-800">
                ✈️ {airline.text}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
