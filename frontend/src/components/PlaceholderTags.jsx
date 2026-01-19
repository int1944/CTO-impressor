export function PlaceholderTags({ nextSlot, intent, onTagClick }) {
  // Define slot mappings for each intent
  const slotMappings = {
    flight: [
      { key: "from", label: "from where" },
      { key: "to", label: "to where" },
      { key: "date", label: "on date" },
      { key: "return", label: "returning on" },
      { key: "time", label: "at time" },
      { key: "class", label: "in class" },
      { key: "airline", label: "on airline" },
    ],
    hotel: [
      { key: "city", label: "in city" },
      { key: "checkin", label: "check-in date" },
      { key: "checkout", label: "check-out date" },
      { key: "guests", label: "for guests" },
      { key: "rooms", label: "how many rooms" },
    ],
    train: [
      { key: "from", label: "from where" },
      { key: "to", label: "to where" },
      { key: "date", label: "on date" },
      { key: "class", label: "in class" },
      { key: "time", label: "at time" },
    ],
    holiday: [
      { key: "to", label: "to destination" },
      { key: "date", label: "starting on" },
      { key: "nights", label: "for days" },
      { key: "travelers", label: "for travelers" },
    ],
  };

  // Get slots for current intent, or show generic slots if no intent
  const slots =
    intent && slotMappings[intent]
      ? slotMappings[intent]
      : [
          { key: "from", label: "from where" },
          { key: "to", label: "to where" },
          { key: "date", label: "on date" },
        ];

  if (!nextSlot || slots.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {slots.map((slot) => {
        const isActive = slot.key === nextSlot;

        return (
          <button
            key={slot.key}
            onClick={() => onTagClick && onTagClick(slot.key)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
              isActive
                ? "bg-red-100 text-red-700 shadow-md ring-2 ring-red-400"
                : "bg-white/80 text-gray-600 hover:bg-white hover:shadow-md"
            }`}
          >
            {slot.label}
          </button>
        );
      })}
    </div>
  );
}
