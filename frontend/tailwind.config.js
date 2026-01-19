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
      },
      boxShadow: {
        'glow': '0 0 20px rgba(241, 106, 34, 0.3)',
        'glow-lg': '0 0 30px rgba(241, 106, 34, 0.4)',
      },
    },
  },
  plugins: [],
}
