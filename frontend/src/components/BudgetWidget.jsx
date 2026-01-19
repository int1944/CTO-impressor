import React from "react";

export function BudgetWidget({ suggestions, onBudgetSelect }) {
  // Default budgets if suggestions are not available
  const defaultBudgets = [
    { id: "budget", label: "Budget", icon: "💰", color: "from-green-50 to-emerald-50 border-green-200/50 hover:from-green-100 hover:to-emerald-100 text-green-700" },
    { id: "affordable", label: "Affordable", icon: "💵", color: "from-blue-50 to-cyan-50 border-blue-200/50 hover:from-blue-100 hover:to-cyan-100 text-blue-700" },
    { id: "mid-range", label: "Mid-Range", icon: "💳", color: "from-yellow-50 to-amber-50 border-yellow-200/50 hover:from-yellow-100 hover:to-amber-100 text-yellow-700" },
    { id: "luxury", label: "Luxury", icon: "💎", color: "from-purple-50 to-pink-50 border-purple-200/50 hover:from-purple-100 hover:to-pink-100 text-purple-700" },
    { id: "premium", label: "Premium", icon: "👑", color: "from-indigo-50 to-violet-50 border-indigo-200/50 hover:from-indigo-100 hover:to-violet-100 text-indigo-700" },
  ];

  // Extract budgets from suggestions or use defaults
  const budgets = suggestions && suggestions.length > 0
    ? suggestions
        .filter((s) => s.selectable && !s.is_placeholder)
        .map((s) => {
          const budgetId = s.text.toLowerCase().replace(/\s+/g, "-");
          const defaultBudget = defaultBudgets.find((b) => b.id === budgetId || b.label.toLowerCase() === s.text.toLowerCase());
          return {
            id: budgetId,
            label: s.text.charAt(0).toUpperCase() + s.text.slice(1),
            icon: defaultBudget?.icon || "💵",
            color: defaultBudget?.color || "from-gray-50 to-slate-50 border-gray-200/50 hover:from-gray-100 hover:to-slate-100 text-gray-700",
          };
        })
    : defaultBudgets;

  const handleClick = (budget) => {
    if (onBudgetSelect) {
      onBudgetSelect(budget.label);
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <span className="text-2xl">💸</span>
        Select Budget
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {budgets.map((budget) => (
          <button
            key={budget.id}
            onClick={() => handleClick(budget)}
            className={`flex flex-col items-center justify-center p-4 rounded-xl bg-gradient-to-br ${budget.color} border transition-all duration-200 hover:scale-105 hover:shadow-md group`}
          >
            <span className="text-3xl mb-2 group-hover:scale-110 transition-transform">
              {budget.icon}
            </span>
            <span className={`text-sm font-medium group-hover:font-semibold`}>
              {budget.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
