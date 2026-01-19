import { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

export function CalendarWidget({ onDateSelect, selectedDate }) {
  const [showCalendar, setShowCalendar] = useState(false);

  const quickOptions = [
    { label: 'Today', value: 'today' },
    { label: 'Tomorrow', value: 'tomorrow' },
    { label: 'This Weekend', value: 'weekend' },
    { label: 'Next Week', value: 'nextweek' },
  ];

  const handleQuickSelect = (option) => {
    const today = new Date();
    let date;

    switch (option) {
      case 'today':
        date = today;
        break;
      case 'tomorrow':
        date = new Date(today);
        date.setDate(date.getDate() + 1);
        break;
      case 'weekend':
        date = new Date(today);
        const dayOfWeek = date.getDay();
        const daysUntilSaturday = 6 - dayOfWeek;
        date.setDate(date.getDate() + daysUntilSaturday);
        break;
      case 'nextweek':
        date = new Date(today);
        date.setDate(date.getDate() + 7);
        break;
      default:
        date = today;
    }

    if (onDateSelect) {
      onDateSelect(date);
    }
    setShowCalendar(false);
  };

  const formatDate = (date) => {
    if (!date) return '';
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="translucent-card rounded-2xl p-4 shadow-lg glow-effect max-w-sm">
      <div className="space-y-3">
        {/* Quick date options */}
        <div className="grid grid-cols-2 gap-2">
          {quickOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => handleQuickSelect(option.value)}
              className="px-4 py-2 rounded-xl bg-white/60 hover:bg-white/80 transition-all duration-200 border border-peach-200 hover:border-peach-400 text-sm font-medium text-gray-800"
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* Calendar picker */}
        <div className="relative">
          <button
            onClick={() => setShowCalendar(!showCalendar)}
            className="w-full px-4 py-2 rounded-xl bg-white/60 hover:bg-white/80 border border-peach-200 text-left text-sm font-medium text-gray-800"
          >
            {selectedDate ? formatDate(selectedDate) : 'Select date'}
          </button>

          {showCalendar && (
            <div className="absolute top-full left-0 mt-2 z-10">
              <DatePicker
                selected={selectedDate}
                onChange={(date) => {
                  if (onDateSelect) {
                    onDateSelect(date);
                  }
                  setShowCalendar(false);
                }}
                inline
                minDate={new Date()}
                className="rounded-xl"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
