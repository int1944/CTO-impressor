import { useMemo } from "react";

export function TimeWidget({ suggestions, onTimeSelect }) {
  // Filter time suggestions
  const timeSuggestions = useMemo(() => {
    return suggestions.filter(
      (s) =>
        !s.is_placeholder &&
        s.selectable &&
        s.entity_type === "time"
    );
  }, [suggestions]);

  if (timeSuggestions.length === 0) {
    return null;
  }

  // Map time text to icons and labels
  const timeConfig = {
    morning: {
      icon: "🌅",
      label: "Morning",
      time: "6 AM - 12 PM",
    },
    afternoon: {
      icon: "☀️",
      label: "Afternoon",
      time: "12 PM - 5 PM",
    },
    evening: {
      icon: "🌆",
      label: "Evening",
      time: "5 PM - 9 PM",
    },
    night: {
      icon: "🌙",
      label: "Night",
      time: "9 PM - 6 AM",
    },
  };

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Select preferred time
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {timeSuggestions.map((time, index) => {
            const config = timeConfig[time.text.toLowerCase()] || {
              icon: "🕐",
              label: time.text.charAt(0).toUpperCase() + time.text.slice(1),
              time: "",
            };

            return (
              <button
                key={`time-${index}`}
                onClick={() => onTimeSelect && onTimeSelect(time)}
                className="flex flex-col items-center justify-center px-4 py-4 rounded-xl bg-white/60 hover:bg-white/80 transition-all duration-200 border border-peach-200 hover:border-peach-400 hover:shadow-md hover:scale-105"
              >
                <span className="text-3xl mb-2">{config.icon}</span>
                <span className="text-sm font-medium text-gray-800 mb-1">
                  {config.label}
                </span>
                {config.time && (
                  <span className="text-xs text-gray-500">{config.time}</span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
