import { useState, useMemo } from "react";
import { TravelInput } from "./components/TravelInput";
import { SuggestionBox } from "./components/SuggestionBox";
import { CalendarWidget } from "./components/CalendarWidget";
import { CityListWidget } from "./components/CityListWidget";
import { IntentWidget } from "./components/IntentWidget";
import { TimeWidget } from "./components/TimeWidget";
import { ClassWidget } from "./components/ClassWidget";
import { NumberWidget } from "./components/NumberWidget";
import { CategoryWidget } from "./components/CategoryWidget";
import { QuotaWidget } from "./components/QuotaWidget";
import { AirlineWidget } from "./components/AirlineWidget";
import { ThemeWidget } from "./components/ThemeWidget";
import { BudgetWidget } from "./components/BudgetWidget";
import { PlaceholderTags } from "./components/PlaceholderTags";
import { useSuggestions } from "./hooks/useSuggestions";
import { insertEntity } from "./utils/queryBuilder";
import mmtLogo from "./assets/Makemytrip_logo.svg";

function App() {
  const [query, setQuery] = useState("");
  const [cursorPosition, setCursorPosition] = useState(0);
  const [selectedDate, setSelectedDate] = useState(null);
  const context = useMemo(() => ({}), []);

  const { suggestions, loading, intent, nextSlot, source, latency } =
    useSuggestions(query, cursorPosition, context);

  const handleQueryChange = (newQuery) => {
    setQuery(newQuery);
  };

  // Helper to get placeholder text from suggestions
  const getPlaceholderText = () => {
    if (suggestions && suggestions.length > 0 && suggestions[0].is_placeholder) {
      return suggestions[0].text;
    }
    return null;
  };

  // Get only clickable entity suggestions (exclude placeholders)
  const getClickableSuggestions = () => {
    if (!suggestions || suggestions.length === 0) return [];
    return suggestions.filter(s => s.selectable && !s.is_placeholder);
  };

  // Format suggestion with placeholder keyword (like test_live.py)
  const formatSuggestionWithPlaceholder = (suggestionText, placeholderText, currentQuery) => {
    if (!placeholderText) {
      return suggestionText;
    }

    const placeholderWords = placeholderText.trim().split(/\s+/);
    const placeholderFirst = placeholderWords[0]?.toLowerCase();
    const placeholderSecond = placeholderWords[1]?.toLowerCase();
    // Check for "starting on" (two words)
    const isStartingOn = placeholderFirst === 'starting' && placeholderSecond === 'on';
    const prefixCandidates = new Set(['from', 'to', 'on', 'at', 'in', 'with', 'for', 'check-in', 'check-out', 'starting']);
    
    if (!placeholderFirst || (!prefixCandidates.has(placeholderFirst) && !isStartingOn)) {
      return suggestionText;
    }

    const suggestionLower = suggestionText.toLowerCase().trim();
    
    // If suggestion already starts with the keyword, don't add it again
    if (isStartingOn) {
      if (suggestionLower.startsWith('starting on ')) {
        return suggestionText;
      }
    } else if (suggestionLower.startsWith(placeholderFirst + ' ')) {
      return suggestionText;
    }

    const queryLower = currentQuery.toLowerCase().trim();
    const queryWords = queryLower.split(/\s+/);
    const lastWord = queryWords[queryWords.length - 1] || "";

    // If user already typed a different slot keyword, don't force the placeholder keyword
    if (prefixCandidates.has(lastWord) && lastWord !== placeholderFirst) {
      return suggestionText;
    }

    // Check if query already ends with the placeholder keyword (with or without space)
    // For "check-in" and "check-out", handle both with and without hyphen
    if (placeholderFirst === 'check-in' || placeholderFirst === 'check-out') {
      const baseWord = placeholderFirst.replace('-', '');
      // Check if query ends with the keyword (with space, without space, or as last word)
      if (lastWord === placeholderFirst || lastWord === baseWord || 
          queryLower.endsWith(' ' + placeholderFirst) || queryLower.endsWith(' ' + baseWord) ||
          queryLower.endsWith(placeholderFirst) || queryLower.endsWith(baseWord)) {
        return suggestionText; // Don't add keyword, user already typed it
      }
    } else {
      // Check if query ends with the keyword (with space, without space, or as last word)
      // This handles cases like "flight from" -> don't add "from" again
      if (lastWord === placeholderFirst || 
          queryLower.endsWith(' ' + placeholderFirst) || 
          queryLower.endsWith(placeholderFirst)) {
        return suggestionText; // Don't add keyword, user already typed it
      }
    }

    // Add the keyword prefix
    if (isStartingOn) {
      return `starting on ${suggestionText}`;
    }
    return `${placeholderFirst} ${suggestionText}`;
  };

  // Format nights selection (like test_live.py)
  const formatNightsSelection = (suggestionText, placeholderText) => {
    if (!placeholderText || !placeholderText.toLowerCase().includes('night')) {
      return suggestionText;
    }

    // If it's already formatted (contains "night" or "nights"), return as-is
    if (suggestionText.toLowerCase().includes('night')) {
      return suggestionText;
    }

    // If it's just a number, format it
    if (/^\d+$/.test(suggestionText)) {
      return suggestionText === "1" ? `${suggestionText} night` : `${suggestionText} nights`;
    }

    return suggestionText;
  };

  // Format number-based selections (passengers, guests, etc.)
  const formatNumberSelection = (suggestionText, entityType) => {
    // If it's already formatted (contains the type word), return as-is
    if (entityType === 'passengers' && /\b(passenger|passengers|traveler|travelers)\b/i.test(suggestionText)) {
      return suggestionText;
    }
    if (entityType === 'guests' && /\b(guest|guests)\b/i.test(suggestionText)) {
      return suggestionText;
    }
    if (entityType === 'rooms' && /\b(room|rooms)\b/i.test(suggestionText)) {
      return suggestionText;
    }

    // If it's just a number, format it with the appropriate word
    if (/^\d+$/.test(suggestionText)) {
      const num = suggestionText;
      if (entityType === 'passengers') {
        return num === "1" ? `${num} passenger` : `${num} passengers`;
      }
      if (entityType === 'guests') {
        return num === "1" ? `${num} guest` : `${num} guests`;
      }
      if (entityType === 'rooms') {
        return num === "1" ? `${num} room` : `${num} rooms`;
      }
    }

    return suggestionText;
  };

  const handleSuggestionClick = (suggestion) => {
    if (!suggestion.selectable || suggestion.is_placeholder) return;

    // Special handling for intent suggestions
    if (suggestion.entity_type === 'intent') {
      // For intent, just append the intent word (e.g., "flight", "hotel", "train", "holiday")
      const trimmedQuery = query.trim();
      let newQuery;
      
      // Handle cases like "book a" -> "book a flight" or "book a holiday package"
      if (trimmedQuery.endsWith(' a') || trimmedQuery === 'a') {
        // For holiday, use "holiday package" instead of just "holiday"
        if (suggestion.text.toLowerCase() === 'holiday') {
          newQuery = trimmedQuery.replace(/\s*a\s*$/, '') + ' holiday package';
        } else {
          newQuery = trimmedQuery.replace(/\s*a\s*$/, '') + ' ' + suggestion.text;
        }
      } else if (trimmedQuery.endsWith('book') || trimmedQuery.includes('want to book')) {
        // For holiday, use "holiday package" instead of just "holiday"
        if (suggestion.text.toLowerCase() === 'holiday') {
          newQuery = trimmedQuery + ' a holiday package';
        } else {
          newQuery = trimmedQuery + ' a ' + suggestion.text;
        }
      } else {
        // For holiday, use "holiday package" if query suggests booking context
        if (suggestion.text.toLowerCase() === 'holiday' && 
            (trimmedQuery.toLowerCase().includes('book') || 
             trimmedQuery.toLowerCase().includes('want') || 
             trimmedQuery.toLowerCase().includes('need'))) {
          newQuery = trimmedQuery ? `${trimmedQuery} holiday package` : 'holiday package';
        } else {
          // Just append the intent
          newQuery = trimmedQuery ? `${trimmedQuery} ${suggestion.text}` : suggestion.text;
        }
      }
      setQuery(newQuery);
      return;
    }

    // Get placeholder text to format suggestion
    const placeholderText = getPlaceholderText();
    
    // Format suggestion with placeholder keyword (like terminal version)
    let formattedText = formatSuggestionWithPlaceholder(
      suggestion.text,
      placeholderText,
      query
    );
    
    // Format nights selection
    formattedText = formatNightsSelection(formattedText, placeholderText);
    
    // Format number-based selections (passengers, guests, rooms)
    formattedText = formatNumberSelection(formattedText, suggestion.entity_type);

    // Insert entity with formatted text
    const newQuery = insertEntity(
      query,
      formattedText,
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
    // Use the correct entity type based on nextSlot
    const entityType =
      nextSlot === "checkin"
        ? "checkin"
        : nextSlot === "checkout"
        ? "checkout"
        : nextSlot === "return"
        ? "return"
        : "date";
    const newQuery = insertEntity(query, dateStr, entityType);
    setQuery(newQuery);
  };

  const handleTagClick = (slotKey, insertText) => {
    if (insertText) {
      const trimmedQuery = query.trim();
      let newQuery;

      if (trimmedQuery.endsWith(" a") && insertText.startsWith("a ")) {
        newQuery = trimmedQuery.slice(0, -2) + " " + insertText;
      } else if (trimmedQuery === "a" && insertText.startsWith("a ")) {
        newQuery = insertText;
      } else if (trimmedQuery.endsWith("a") && insertText.startsWith("a ")) {
        newQuery = trimmedQuery.slice(0, -1) + insertText;
      } else {
        newQuery = trimmedQuery ? `${trimmedQuery} ${insertText}` : insertText;
      }

      setQuery(newQuery);
      return;
    }

    const slotKeywordMap = {
      from: "from",
      to: "to",
      date: "on",
      return: "returning on",
      time: "at",
      class: "in",
      airline: "on",
      city: "in",
      checkin: "check-in",
      checkout: "check-out",
      guests: "for",
      rooms: "for",
      nights: "for",
      category: "in",
      quota: "in",
      theme: "",  // No keyword for theme
      budget: "",  // No keyword for budget
    };

    const keyword = slotKeywordMap[slotKey];
    if (keyword) {
      const trimmedQuery = query.trim();
      const newQuery = trimmedQuery ? `${trimmedQuery} ${keyword}` : keyword;
      setQuery(newQuery);
    }
  };


  const handleSubmit = (finalQuery) => {
    console.log("Submitting query:", finalQuery);
    // Handle submission (e.g., navigate to results page)
    alert(`Query submitted: ${finalQuery}`);
  };

  // Determine which widget to show
  const showCalendar =
    nextSlot === "date" || nextSlot === "checkin" || nextSlot === "checkout" || nextSlot === "return";
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
  const showIntentWidget =
    nextSlot === "intent" ||
    suggestions.some(
      (s) => s.entity_type === "intent" && !s.is_placeholder
    );
  const showTimeWidget =
    nextSlot === "time" ||
    suggestions.some(
      (s) => s.entity_type === "time" && !s.is_placeholder
    );
  const showClassWidget =
    nextSlot === "class" ||
    suggestions.some(
      (s) => s.entity_type === "class" && !s.is_placeholder
    );
  const showPassengersWidget =
    nextSlot === "passengers" ||
    suggestions.some(
      (s) => s.entity_type === "passengers" && !s.is_placeholder
    );
  const showGuestsWidget =
    nextSlot === "guests" ||
    suggestions.some(
      (s) => s.entity_type === "guests" && !s.is_placeholder
    );
  const showNightsWidget =
    nextSlot === "nights" ||
    suggestions.some(
      (s) => s.entity_type === "nights" && !s.is_placeholder
    );
  const showRoomsWidget =
    nextSlot === "rooms" ||
    suggestions.some(
      (s) => s.entity_type === "rooms" && !s.is_placeholder
    );
  const showCategoryWidget =
    nextSlot === "category" ||
    suggestions.some(
      (s) => s.entity_type === "category" && !s.is_placeholder
    );
  const showQuotaWidget =
    nextSlot === "quota" ||
    suggestions.some(
      (s) => s.entity_type === "quota" && !s.is_placeholder
    );
  const showAirlineWidget =
    nextSlot === "airline" ||
    suggestions.some(
      (s) => s.entity_type === "airline" && !s.is_placeholder
    );
  const showThemeWidget =
    nextSlot === "theme" ||
    suggestions.some(
      (s) => s.entity_type === "theme" && !s.is_placeholder
    );
  const showBudgetWidget =
    nextSlot === "budget" ||
    suggestions.some(
      (s) => s.entity_type === "budget" && !s.is_placeholder
    );

  const hasWidgetForNextSlot =
    showIntentWidget ||
    showCalendar ||
    showCityWidget ||
    showTimeWidget ||
    showClassWidget ||
    showPassengersWidget ||
    showGuestsWidget ||
    showNightsWidget ||
    showRoomsWidget ||
    showCategoryWidget ||
    showQuotaWidget ||
    showAirlineWidget ||
    showThemeWidget ||
    showBudgetWidget;

  // Inline suggestions only when no dedicated widget applies
  const showInlineSuggestions = !hasWidgetForNextSlot;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 pb-40 relative">
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
              placeholder={getPlaceholderText()}
              suggestions={showInlineSuggestions ? getClickableSuggestions() : []}
            />
            <PlaceholderTags
              nextSlot={nextSlot}
              intent={intent}
              onTagClick={handleTagClick}
              suggestions={suggestions}
              query={query}
            />

          </div>

           {/* Widgets Section */}
           <div className="flex flex-wrap gap-4 justify-center">
             {/* Intent Widget */}
            {showIntentWidget && !showInlineSuggestions && (
               <IntentWidget
                 suggestions={suggestions}
                 onIntentSelect={handleSuggestionClick}
               />
             )}

             {/* Calendar Widget */}
             {showCalendar && (
               <CalendarWidget
                 onDateSelect={handleDateSelect}
                 selectedDate={selectedDate}
               />
             )}

             {/* City List Widget - Hide when inline suggestions are showing */}
            {showCityWidget && !showInlineSuggestions && (
               <CityListWidget
                 suggestions={suggestions}
                 onCitySelect={handleSuggestionClick}
                 entityType={nextSlot}
               />
             )}

             {/* Time Widget - Hide when inline suggestions showing */}
            {showTimeWidget && !showInlineSuggestions && (
               <TimeWidget
                 suggestions={suggestions}
                 onTimeSelect={handleSuggestionClick}
               />
             )}

             {/* Class Widget - Hide when inline suggestions showing */}
            {showClassWidget && !showInlineSuggestions && (
               <ClassWidget
                 suggestions={suggestions}
                 onClassSelect={handleSuggestionClick}
                 intent={intent}
               />
             )}

             {/* Passengers Widget - Hide when inline suggestions showing */}
            {showPassengersWidget && !showInlineSuggestions && (
               <NumberWidget
                 suggestions={suggestions}
                 onNumberSelect={handleSuggestionClick}
                 slotType="passengers"
               />
             )}

             {/* Guests Widget - Hide when inline suggestions showing */}
            {showGuestsWidget && !showInlineSuggestions && (
               <NumberWidget
                 suggestions={suggestions}
                 onNumberSelect={handleSuggestionClick}
                 slotType="guests"
               />
             )}

             {/* Nights Widget - Hide when inline suggestions showing */}
            {showNightsWidget && !showInlineSuggestions && (
               <NumberWidget
                 suggestions={suggestions}
                 onNumberSelect={handleSuggestionClick}
                 slotType="nights"
               />
             )}

             {/* Rooms Widget - Hide when inline suggestions showing */}
            {showRoomsWidget && !showInlineSuggestions && (
               <NumberWidget
                 suggestions={suggestions}
                 onNumberSelect={handleSuggestionClick}
                 slotType="rooms"
               />
             )}

             {/* Category Widget - Hide when inline suggestions showing */}
            {showCategoryWidget && !showInlineSuggestions && (
               <CategoryWidget
                 suggestions={suggestions}
                 onCategorySelect={handleSuggestionClick}
               />
             )}

             {/* Quota Widget - Hide when inline suggestions showing */}
            {showQuotaWidget && !showInlineSuggestions && (
               <QuotaWidget
                 suggestions={suggestions}
                 onQuotaSelect={handleSuggestionClick}
               />
             )}

             {/* Airline Widget - Hide when inline suggestions showing */}
            {showAirlineWidget && !showInlineSuggestions && (
               <AirlineWidget
                 suggestions={suggestions}
                 onAirlineSelect={handleSuggestionClick}
               />
             )}

             {/* Theme Widget - Hide when inline suggestions showing */}
            {showThemeWidget && !showInlineSuggestions && (
               <ThemeWidget
                 suggestions={suggestions}
                 onThemeSelect={(theme) => {
                   handleSuggestionClick({
                     text: theme,
                     entity_type: "theme",
                     selectable: true,
                     is_placeholder: false,
                   });
                 }}
               />
             )}

             {/* Budget Widget - Hide when inline suggestions showing */}
            {showBudgetWidget && !showInlineSuggestions && (
               <BudgetWidget
                 suggestions={suggestions}
                 onBudgetSelect={(budget) => {
                   handleSuggestionClick({
                     text: budget,
                     entity_type: "budget",
                     selectable: true,
                     is_placeholder: false,
                   });
                 }}
               />
             )}
           </div>
        </div>

        {/* Suggestion Box (Floating) - Only show when no specialized widget is active */}
        {suggestions.length > 0 && 
         !showInlineSuggestions &&
         !showIntentWidget && 
         !showCalendar && 
         !showCityWidget && 
         !showTimeWidget && 
         !showClassWidget && 
         !showPassengersWidget && 
         !showGuestsWidget && 
         !showNightsWidget && 
         !showRoomsWidget && 
         !showCategoryWidget && 
         !showQuotaWidget && 
         !showAirlineWidget &&
         !showThemeWidget &&
         !showBudgetWidget && (
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
          <div className="fixed bottom-4 left-4 z-10 pointer-events-none max-w-xs">
            <div className="glass-card rounded-xl text-xs text-white/80 p-4">
              <div>Intent: {intent || "None"}</div>
              <div>Next Slot: {nextSlot || "None"}</div>
              <div>Source: {source || "None"}</div>
              <div>Latency: {latency}ms</div>
              <div>Suggestions: {suggestions.length}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
