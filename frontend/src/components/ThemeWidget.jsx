import React from "react";

export function ThemeWidget({ suggestions, onThemeSelect }) {
  // Default themes if suggestions are not available
  const defaultThemes = [
    { id: "honeymoon", label: "Honeymoon", icon: "💑" },
    { id: "adventure", label: "Adventure", icon: "🏔️" },
    { id: "beach", label: "Beach", icon: "🏖️" },
    { id: "family", label: "Family", icon: "👨‍👩‍👧‍👦" },
    { id: "mountains", label: "Mountains", icon: "⛰️" },
    { id: "cultural", label: "Cultural", icon: "🏛️" },
    { id: "romantic", label: "Romantic", icon: "🌹" },
    { id: "wildlife", label: "Wildlife", icon: "🦁" },
  ];

  // Extract themes from suggestions or use defaults
  const themes = suggestions && suggestions.length > 0
    ? suggestions
        .filter((s) => s.selectable && !s.is_placeholder)
        .map((s) => {
          const themeId = s.text.toLowerCase();
          const defaultTheme = defaultThemes.find((t) => t.id === themeId);
          return {
            id: themeId,
            label: s.text.charAt(0).toUpperCase() + s.text.slice(1),
            icon: defaultTheme?.icon || "🎯",
          };
        })
    : defaultThemes;

  const handleClick = (theme) => {
    if (onThemeSelect) {
      onThemeSelect(theme.label);
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <span className="text-2xl">🎨</span>
        Select Theme
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {themes.map((theme) => (
          <button
            key={theme.id}
            onClick={() => handleClick(theme)}
            className="flex flex-col items-center justify-center p-4 rounded-xl bg-gradient-to-br from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100 border border-purple-200/50 transition-all duration-200 hover:scale-105 hover:shadow-md group"
          >
            <span className="text-3xl mb-2 group-hover:scale-110 transition-transform">
              {theme.icon}
            </span>
            <span className="text-sm font-medium text-gray-700 group-hover:text-purple-700">
              {theme.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
