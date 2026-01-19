/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        peach: {
          50: '#fef5f0',
          100: '#fde8d8',
          200: '#fbd0b0',
          300: '#f8b07e',
          400: '#f48a4a',
          500: '#f16a22',
          600: '#e24f18',
          700: '#bb3c16',
          800: '#95321a',
          900: '#782c18',
        },
        mmt: {
          blue: '#008cff',
          purple: '#764ba2',
          indigo: '#667eea',
          red: '#eb2026', // Official MakeMyTrip red
          gray: '#4a4a4a', // Logo background gray
        },
      },
      boxShadow: {
        'glow': '0 0 30px rgba(255, 255, 255, 0.2)',
        'glow-lg': '0 0 40px rgba(255, 255, 255, 0.3)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'pulse': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
