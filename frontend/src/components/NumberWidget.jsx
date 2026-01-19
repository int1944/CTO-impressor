import { useMemo } from "react";

export function NumberWidget({ suggestions, onNumberSelect, slotType }) {
  // Filter number suggestions (passengers, guests, nights, etc.)
  const numberSuggestions = useMemo(() => {
    return suggestions.filter(
      (s) =>
        !s.is_placeholder &&
        s.selectable &&
        (s.entity_type === slotType)
    );
  }, [suggestions, slotType]);

  if (numberSuggestions.length === 0) {
    return null;
  }

  // Get label based on slot type
  const getLabel = (type) => {
    const labels = {
      passengers: "Number of passengers",
      guests: "Number of guests",
      nights: "Number of nights",
      rooms: "Number of rooms",
    };
    return labels[type] || "Select number";
  };

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          {getLabel(slotType)}
        </h3>
        <div className="grid grid-cols-4 gap-2">
          {numberSuggestions.map((number, index) => {
            const isFamily = number.text.toLowerCase() === "family";
            // Extract just the number if text includes words (e.g., "2 guests" -> "2")
            const numberMatch = number.text.match(/^(\d+)/);
            const displayNumber = numberMatch ? numberMatch[1] : number.text;
            
            return (
              <button
                key={`number-${index}`}
                onClick={() => onNumberSelect && onNumberSelect(number)}
                className={`flex flex-col items-center justify-center px-3 py-3 rounded-xl transition-all duration-200 border-2 hover:shadow-md hover:scale-105 ${
                  isFamily
                    ? "bg-purple-100 border-purple-300 hover:bg-purple-200"
                    : "bg-white/60 border-peach-200 hover:bg-white/80 hover:border-peach-400"
                }`}
              >
                {isFamily ? (
                  <>
                    <span className="text-2xl mb-1">👨‍👩‍👧‍👦</span>
                    <span className="text-xs font-medium text-gray-800">Family</span>
                  </>
                ) : (
                  <>
                    <span className="text-xl font-bold text-gray-800">{displayNumber}</span>
                    {/* Show the full text if it includes words, otherwise add label */}
                    {number.text.includes(" ") ? (
                      <span className="text-xs text-gray-500">{number.text.split(" ")[1]}</span>
                    ) : (
                      <>
                        {slotType === "nights" && (
                          <span className="text-xs text-gray-500">
                            {displayNumber === "1" ? "night" : "nights"}
                          </span>
                        )}
                        {slotType === "guests" && (
                          <span className="text-xs text-gray-500">
                            {displayNumber === "1" ? "guest" : "guests"}
                          </span>
                        )}
                        {slotType === "passengers" && (
                          <span className="text-xs text-gray-500">
                            {displayNumber === "1" ? "passenger" : "passengers"}
                          </span>
                        )}
                      </>
                    )}
                  </>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
