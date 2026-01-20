export function PlaceholderTags({ nextSlot, intent, onTagClick, suggestions = [], query = "" }) {
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
      { key: "passengers", label: "for travelers" },
      { key: "theme", label: "theme" },
      { key: "budget", label: "budget" },
    ],
  };

  // Only show intent selection buttons when no intent is detected
  if (!intent) {
    // Hide intent buttons if user has typed anything
    if (query && query.trim().length > 0) {
      return null;
    }
    
    // Get intent suggestions from API if available, otherwise use defaults
    const intentSuggestions = suggestions
      .filter(s => s.entity_type === 'intent' && s.selectable && !s.is_placeholder)
      .map(s => s.text.toLowerCase());
    
    // Default intent options
    const defaultIntents = ['flight', 'hotel', 'train', 'holiday'];
    
    // Use API suggestions if available, otherwise use defaults
    const availableIntents = intentSuggestions.length > 0 ? intentSuggestions : defaultIntents;
    
    const intentConfig = {
      flight: { label: "Flights", insertText: "Book a flight" },
      hotel: { label: "Hotels", insertText: "Book a hotel" },
      train: { label: "Trains", insertText: "Book a train" },
      holiday: { label: "Holidays", insertText: "Book a holiday package" },
    };
    
    const intentOptions = availableIntents
      .filter(intent => intentConfig[intent])
      .map(intent => ({
        key: intent,
        label: intentConfig[intent].label,
        insertText: intentConfig[intent].insertText,
      }));
    
    if (intentOptions.length === 0) {
      return null;
    }
    
    return (
      <div className="flex flex-wrap gap-2 mt-3 justify-center">
        {intentOptions.map((option) => (
          <button
            key={option.key}
            onClick={() => onTagClick && onTagClick(option.key, option.insertText)}
            className="px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-200 bg-blue-100 text-blue-700 hover:bg-blue-200 hover:shadow-md"
          >
            {option.label}
          </button>
        ))}
      </div>
    );
  }

  // Get slots for current intent
  const slots = intent && slotMappings[intent] ? slotMappings[intent] : [];

  // Show slots for the detected intent
  if (slots.length === 0) {
    return null;
  }

  const activeSlot = slots.find((slot) => slot.key === nextSlot);
  if (!activeSlot) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2 mt-3 justify-center">
      <div
        key={activeSlot.key}
        className="px-5 py-2.5 rounded-full text-sm font-semibold bg-red-100 text-red-700 shadow-md ring-2 ring-red-400 cursor-default"
      >
        {activeSlot.label}
      </div>
    </div>
  );
}