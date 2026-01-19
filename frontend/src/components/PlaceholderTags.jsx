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

  // Get slots for current intent, or show intent options if no intent
const slots =
intent && slotMappings[intent]
  ? slotMappings[intent]
  : [
      { key: "flight", label: "Flights", insertText: "Book a flight" },
      { key: "hotel", label: "Hotels", insertText: "Book a hotel" },
      { key: "train", label: "Trains", insertText: "Book a train" },
      { key: "holiday", label: "Holidays", insertText: "Book a holiday package" },
    ];

if (!nextSlot && !intent) {
// Show intent selection when no intent is determined
return (
  <div className="flex flex-wrap gap-2 mt-3">
    {slots.map((slot) => (
      <button
        key={slot.key}
        onClick={() => onTagClick && onTagClick(slot.key, slot.insertText)}
        className="px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 bg-blue-100 text-blue-700 hover:bg-blue-200 hover:shadow-md"
      >
        {slot.label}
      </button>
    ))}
  </div>
);
}

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
                ? "bg-pink-200 text-pink-800 shadow-md"
                : "bg-gray-100 text-gray-500 hover:bg-gray-200"
            }`}
          >
            {slot.label}
          </button>
        );
      })}
    </div>
  );
}
