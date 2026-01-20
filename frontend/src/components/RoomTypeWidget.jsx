import { useMemo } from "react";

export function RoomTypeWidget({ suggestions, onRoomTypeSelect }) {
  // Filter room type suggestions
  const roomTypeSuggestions = useMemo(() => {
    return suggestions.filter(
      (s) =>
        !s.is_placeholder &&
        s.selectable &&
        s.entity_type === "room_type"
    );
  }, [suggestions]);

  if (roomTypeSuggestions.length === 0) {
    return null;
  }

  // Map room type text to icons and labels
  const roomTypeConfig = {
    "single room": { icon: "🛏️", label: "Single Room", desc: "1 person" },
    "double room": { icon: "🛏️🛏️", label: "Double Room", desc: "2 people" },
    suite: { icon: "🏰", label: "Suite", desc: "Luxury" },
    "deluxe room": { icon: "✨", label: "Deluxe Room", desc: "Premium" },
  };

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Select room type
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {roomTypeSuggestions.map((roomType, index) => {
            const config = roomTypeConfig[roomType.text.toLowerCase()] || {
              icon: "🛏️",
              label: roomType.text,
              desc: "",
            };

            return (
              <button
                key={`room-type-${index}`}
                onClick={() => onRoomTypeSelect && onRoomTypeSelect(roomType)}
                className="flex flex-col items-center justify-center px-4 py-4 rounded-xl bg-white/60 hover:bg-white/80 transition-all duration-200 border border-peach-200 hover:border-peach-400 hover:shadow-md hover:scale-105"
              >
                <span className="text-3xl mb-2">{config.icon}</span>
                <span className="text-sm font-medium text-gray-800 mb-1">
                  {config.label}
                </span>
                {config.desc && (
                  <span className="text-xs text-gray-500">{config.desc}</span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
