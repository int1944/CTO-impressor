import { useMemo } from "react";

export function ClassWidget({ suggestions, onClassSelect, intent }) {
  // Filter class suggestions
  const classSuggestions = useMemo(() => {
    return suggestions.filter(
      (s) =>
        !s.is_placeholder &&
        s.selectable &&
        s.entity_type === "class"
    );
  }, [suggestions]);

  if (classSuggestions.length === 0) {
    return null;
  }

  // Map class text to icons and labels based on intent
  const getClassConfig = (classText, intentType) => {
    const classLower = classText.toLowerCase();
    
    if (intentType === "flight") {
      const flightClasses = {
        economy: { icon: "💺", label: "Economy", desc: "Standard seating" },
        business: { icon: "🛫", label: "Business", desc: "Premium comfort" },
        first: { icon: "✨", label: "First Class", desc: "Luxury experience" },
        "premium economy": { icon: "🌟", label: "Premium Economy", desc: "Extra legroom" },
      };
      return flightClasses[classLower] || { icon: "💺", label: classText, desc: "" };
    } else if (intentType === "train") {
      const trainClasses = {
        sleeper: { icon: "🛏️", label: "Sleeper", desc: "Berth available" },
        "3ac": { icon: "🚂", label: "3AC", desc: "3-tier AC" },
        "2ac": { icon: "🚆", label: "2AC", desc: "2-tier AC" },
        "1ac": { icon: "✨", label: "1AC", desc: "1-tier AC" },
        general: { icon: "🚃", label: "General", desc: "Unreserved" },
      };
      return trainClasses[classLower] || { icon: "🚂", label: classText, desc: "" };
    }
    
    return { icon: "💺", label: classText, desc: "" };
  };

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Select travel class
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {classSuggestions.map((classOption, index) => {
            const config = getClassConfig(classOption.text, intent);

            return (
              <button
                key={`class-${index}`}
                onClick={() => onClassSelect && onClassSelect(classOption)}
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
