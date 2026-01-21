import { useMemo } from "react";

export function AmenitiesWidget({ suggestions, onAmenitySelect }) {
  // Filter amenities suggestions
  const amenitiesSuggestions = useMemo(() => {
    return suggestions.filter(
      (s) =>
        !s.is_placeholder &&
        s.selectable &&
        s.entity_type === "amenities"
    );
  }, [suggestions]);

  if (amenitiesSuggestions.length === 0) {
    return null;
  }

  // Map amenity text to icons and labels
  const amenityConfig = {
    "swimming pool": { icon: "🏊", label: "Swimming Pool" },
    "pool": { icon: "🏊", label: "Swimming Pool" },
    "wifi": { icon: "📶", label: "WiFi" },
    "wi-fi": { icon: "📶", label: "WiFi" },
    "gym": { icon: "💪", label: "Gym" },
    "fitness center": { icon: "💪", label: "Fitness Center" },
    "spa": { icon: "🧘", label: "Spa" },
    "parking": { icon: "🅿️", label: "Parking" },
    "restaurant": { icon: "🍽️", label: "Restaurant" },
    "bar": { icon: "🍸", label: "Bar" },
    "room service": { icon: "🛎️", label: "Room Service" },
    "air conditioning": { icon: "❄️", label: "AC" },
    "ac": { icon: "❄️", label: "AC" },
    "breakfast": { icon: "🍳", label: "Breakfast" },
    "laundry": { icon: "👔", label: "Laundry" },
    "business center": { icon: "💼", label: "Business Center" },
    "pet friendly": { icon: "🐾", label: "Pet Friendly" },
    "beach access": { icon: "🏖️", label: "Beach Access" },
    "balcony": { icon: "🌅", label: "Balcony" },
    "kitchen": { icon: "🍳", label: "Kitchen" },
    "jacuzzi": { icon: "🛁", label: "Jacuzzi" },
    "tv": { icon: "📺", label: "TV" },
    "minibar": { icon: "🍾", label: "Minibar" },
    "safe": { icon: "🔒", label: "Safe" },
  };

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-2xl">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Select amenities
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
          {amenitiesSuggestions.map((amenity, index) => {
            const amenityLower = amenity.text.toLowerCase();
            const config = amenityConfig[amenityLower] || {
              icon: "✨",
              label: amenity.text,
            };

            return (
              <button
                key={`amenity-${index}`}
                onClick={() => onAmenitySelect && onAmenitySelect(amenity)}
                className="flex flex-col items-center justify-center px-3 py-3 rounded-xl bg-white/60 hover:bg-white/80 transition-all duration-200 border border-peach-200 hover:border-peach-400 hover:shadow-md hover:scale-105"
              >
                <span className="text-2xl mb-1">{config.icon}</span>
                <span className="text-xs font-medium text-gray-800 text-center">
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
