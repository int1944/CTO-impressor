import { useMemo } from "react";

export function IntentWidget({ suggestions, onIntentSelect }) {
  // Filter intent suggestions
  const intentSuggestions = useMemo(() => {
    return suggestions.filter(
      (s) =>
        !s.is_placeholder &&
        s.selectable &&
        s.entity_type === "intent"
    );
  }, [suggestions]);

  if (intentSuggestions.length === 0) {
    return null;
  }

  // Map intent text to icons and colors
  const intentConfig = {
    flight: {
      icon: "✈️",
      label: "Flight",
      color: "bg-blue-100 border-blue-300 hover:bg-blue-200",
    },
    hotel: {
      icon: "🏨",
      label: "Hotel",
      color: "bg-green-100 border-green-300 hover:bg-green-200",
    },
    train: {
      icon: "🚆",
      label: "Train",
      color: "bg-orange-100 border-orange-300 hover:bg-orange-200",
    },
    holiday: {
      icon: "🏖️",
      label: "Holiday",
      color: "bg-purple-100 border-purple-300 hover:bg-purple-200",
    },
  };

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          What would you like to book?
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {intentSuggestions.map((intent, index) => {
            const config = intentConfig[intent.text.toLowerCase()] || {
              icon: "📋",
              label: intent.text.charAt(0).toUpperCase() + intent.text.slice(1),
              color: "bg-gray-100 border-gray-300 hover:bg-gray-200",
            };

            return (
              <button
                key={`intent-${index}`}
                onClick={() => onIntentSelect && onIntentSelect(intent)}
                className={`flex flex-col items-center justify-center px-4 py-4 rounded-xl border-2 transition-all duration-200 hover:shadow-md hover:scale-105 ${config.color}`}
              >
                <span className="text-3xl mb-2">{config.icon}</span>
                <span className="text-sm font-medium text-gray-800">
                  {config.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
