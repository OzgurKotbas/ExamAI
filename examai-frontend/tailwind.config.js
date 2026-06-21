/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        primary: {
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        dark: {
          800: '#0f172a',
          850: '#0d1425',
          900: '#080d1a',
          950: '#050a14',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
  safelist: [
    // Quiz result card colors – used dynamically, must not be purged
    'bg-red-500', 'bg-orange-500', 'bg-green-500',
    'bg-red-50', 'bg-orange-50', 'bg-green-50',
    'border-red-200', 'border-orange-200', 'border-green-200',
    'border-red-500', 'border-orange-500', 'border-green-500',
    'bg-red-900/20', 'bg-orange-900/20', 'bg-green-900/20',
    'dark:bg-red-950/20', 'dark:bg-orange-950/20', 'dark:bg-green-950/20',
    'dark:border-red-800', 'dark:border-orange-800', 'dark:border-green-800',
    'text-red-500', 'text-orange-500', 'text-green-500',
  ],
}
