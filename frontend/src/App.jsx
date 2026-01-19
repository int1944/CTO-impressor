import { useState } from "react";
import { TravelInput } from "./components/TravelInput";
import { SuggestionBox } from "./components/SuggestionBox";
import { PlaceholderTags } from "./components/PlaceholderTags";
import { CalendarWidget } from "./components/CalendarWidget";
import { CityListWidget } from "./components/CityListWidget";
import { useSuggestions } from "./hooks/useSuggestions";
import { insertEntity } from "./utils/queryBuilder";

function App() {
  const [query, setQuery] = useState("");
  const [cursorPosition, setCursorPosition] = useState(0);
  const [selectedDate, setSelectedDate] = useState(null);

  const { suggestions, loading, intent, nextSlot, source, latency } =
    useSuggestions(query, cursorPosition, {});

  const handleQueryChange = (newQuery) => {
    setQuery(newQuery);
  };

  const handleSuggestionClick = (suggestion) => {
    if (!suggestion.selectable || suggestion.is_placeholder) return;

    const newQuery = insertEntity(
      query,
      suggestion.text,
      suggestion.entity_type
    );
    setQuery(newQuery);

    // Focus back on input (will be handled by TravelInput)
  };

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    const dateStr = date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
    const newQuery = insertEntity(query, dateStr, "date");
    setQuery(newQuery);
  };

  const handleTagClick = (slotKey) => {
    // This could trigger a specific widget or add placeholder text
    console.log("Tag clicked:", slotKey);
  };

  const handleSubmit = (finalQuery) => {
    console.log("Submitting query:", finalQuery);
    // Handle submission (e.g., navigate to results page)
    alert(`Query submitted: ${finalQuery}`);
  };

  // Determine which widget to show
  const showCalendar =
    nextSlot === "date" || nextSlot === "checkin" || nextSlot === "checkout";
  const showCityWidget =
    nextSlot === "to" ||
    nextSlot === "from" ||
    nextSlot === "city" ||
    suggestions.some(
      (s) =>
        (s.entity_type === "to" ||
          s.entity_type === "from" ||
          s.entity_type === "city") &&
        !s.is_placeholder
    );

  return (
    <div className="min-h-screen bg-peach-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-4xl space-y-6">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-peach-800 mb-2">
            Travel Booking Assistant
          </h1>
          <p className="text-gray-600">
            Tell us where you want to go and we'll help you plan your trip
          </p>
        </div>

        {/* Suggestion Box (Top Left) */}
        {suggestions.length > 0 && (
          <div className="flex justify-start">
            <SuggestionBox
              suggestions={suggestions}
              onSuggestionClick={handleSuggestionClick}
              loading={loading}
            />
          </div>
        )}

        {/* Main Input Field */}
        <div className="flex flex-col items-center space-y-4">
          <TravelInput
            query={query}
            onQueryChange={handleQueryChange}
            onSuggestionSelect={handleSuggestionClick}
            onSubmit={handleSubmit}
            cursorPosition={cursorPosition}
            onCursorChange={setCursorPosition}
          />

          {/* Placeholder Tags */}
          {nextSlot && (
            <PlaceholderTags
              nextSlot={nextSlot}
              intent={intent}
              onTagClick={handleTagClick}
            />
          )}
        </div>

        {/* Widgets Section */}
        <div className="flex flex-wrap gap-4 justify-center mt-6">
          {/* Calendar Widget */}
          {showCalendar && (
            <CalendarWidget
              onDateSelect={handleDateSelect}
              selectedDate={selectedDate}
            />
          )}

          {/* City List Widget */}
          {showCityWidget && (
            <CityListWidget
              suggestions={suggestions}
              onCitySelect={handleSuggestionClick}
              entityType={nextSlot}
            />
          )}
        </div>

        {/* Debug Info (can be removed in production) */}
        {process.env.NODE_ENV === "development" && (
          <div className="mt-8 p-4 bg-white/60 rounded-xl text-xs text-gray-600">
            <div>Intent: {intent || "None"}</div>
            <div>Next Slot: {nextSlot || "None"}</div>
            <div>Source: {source || "None"}</div>
            <div>Latency: {latency}ms</div>
            <div>Suggestions: {suggestions.length}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
