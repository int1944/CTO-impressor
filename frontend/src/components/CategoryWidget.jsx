import { useMemo } from "react";

export function CategoryWidget({ suggestions, onCategorySelect }) {
  // Filter category suggestions
  const categorySuggestions = useMemo(() => {
    return suggestions.filter(
      (s) =>
        !s.is_placeholder &&
        s.selectable &&
        s.entity_type === "category"
    );
  }, [suggestions]);

  if (categorySuggestions.length === 0) {
    return null;
  }

  // Map category text to icons and labels
  const categoryConfig = {
    budget: { icon: "💰", label: "Budget", desc: "Affordable stays" },
    "3-star": { icon: "⭐", label: "3 Star", desc: "Comfortable" },
    "4-star": { icon: "⭐⭐", label: "4 Star", desc: "Premium" },
    "5-star": { icon: "⭐⭐⭐", label: "5 Star", desc: "Luxury" },
    luxury: { icon: "✨", label: "Luxury", desc: "Top tier" },
  };

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Select hotel category
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {categorySuggestions.map((category, index) => {
            const config = categoryConfig[category.text.toLowerCase()] || {
              icon: "🏨",
              label: category.text,
              desc: "",
            };

            return (
              <button
                key={`category-${index}`}
                onClick={() => onCategorySelect && onCategorySelect(category)}
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
