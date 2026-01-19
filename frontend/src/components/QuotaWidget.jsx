import { useMemo } from "react";

export function QuotaWidget({ suggestions, onQuotaSelect }) {
  // Filter quota suggestions
  const quotaSuggestions = useMemo(() => {
    return suggestions.filter(
      (s) =>
        !s.is_placeholder &&
        s.selectable &&
        s.entity_type === "quota"
    );
  }, [suggestions]);

  if (quotaSuggestions.length === 0) {
    return null;
  }

  // Map quota text to icons and labels
  const quotaConfig = {
    general: { icon: "🎫", label: "General", desc: "Regular booking" },
    tatkal: { icon: "⚡", label: "Tatkal", desc: "Last minute" },
    ladies: { icon: "👩", label: "Ladies", desc: "Women's quota" },
    "senior citizen": { icon: "👴", label: "Senior Citizen", desc: "60+ years" },
  };

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-md">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Select quota type
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {quotaSuggestions.map((quota, index) => {
            const config = quotaConfig[quota.text.toLowerCase()] || {
              icon: "🎫",
              label: quota.text,
              desc: "",
            };

            return (
              <button
                key={`quota-${index}`}
                onClick={() => onQuotaSelect && onQuotaSelect(quota)}
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
