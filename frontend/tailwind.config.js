/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        secondary: {
          50: '#fef7ff',
          100: '#fce7ff',
          500: '#d946ef',
          600: '#c026d3',
          700: '#a21caf',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
      },
      fontFamily: {
        'child-friendly': ['Comic Sans MS', 'cursive', 'system-ui'],
        'hebrew': ['Arial', 'Hebrew', 'sans-serif'],
      },
      fontSize: {
        'child-sm': ['18px', '1.6'],
        'child-base': ['22px', '1.6'],
        'child-lg': ['26px', '1.6'],
        'child-xl': ['30px', '1.6'],
      },
      borderRadius: {
        'child': '16px',
      },
      boxShadow: {
        'child': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'child-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      },
    },
  },
  plugins: [],
}