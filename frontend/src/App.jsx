import { useState } from "react";
import { TravelInput } from "./components/TravelInput";
import { SuggestionBox } from "./components/SuggestionBox";
import { PlaceholderTags } from "./components/PlaceholderTags";
import { CalendarWidget } from "./components/CalendarWidget";
import { CityListWidget } from "./components/CityListWidget";
import { useSuggestions } from "./hooks/useSuggestions";
import { insertEntity } from "./utils/queryBuilder";
import mmtLogo from "./assets/Makemytrip_logo.svg";

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
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative">
      {/* Floating decorative elements */}
      <div className="absolute top-20 left-10 w-64 h-64 bg-white/10 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-300/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
      
      <div className="w-full max-w-4xl space-y-6 z-10">
        {/* Header */}
        <div className="text-center mb-10 animate-fade-in">
          {/* MakeMyTrip Logo - Official Logo */}
          <div className="flex items-center justify-center mb-6">
            <img 
              src={mmtLogo} 
              alt="MakeMyTrip" 
              className="h-14 w-auto drop-shadow-2xl"
            />
          </div>
          <p className="text-white/95 text-xl font-medium drop-shadow-lg">
            Tell us where you want to go and we'll help you plan your trip
          </p>
        </div>

        {/* Main Card Container */}
        <div className="glass-card rounded-3xl p-8 shadow-2xl animate-fade-in">
          {/* Main Input Field */}
          <div className="flex flex-col items-center space-y-4 mb-6">
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
          <div className="flex flex-wrap gap-4 justify-center">
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
        </div>

        {/* Suggestion Box (Floating) */}
        {suggestions.length > 0 && (
          <div className="flex justify-center animate-fade-in">
            <SuggestionBox
              suggestions={suggestions}
              onSuggestionClick={handleSuggestionClick}
              loading={loading}
            />
          </div>
        )}

        {/* Debug Info (can be removed in production) */}
        {process.env.NODE_ENV === "development" && (
          <div className="mt-8 p-4 glass-card rounded-xl text-xs text-white/80">
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
