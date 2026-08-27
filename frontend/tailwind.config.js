/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        wealth: {
          bg: '#F7F4EC',          // Warm Ivory Background
          card: '#FFFEF9',        // Crisp Ivory Card Surface
          surface: '#FDFBF7',     // Secondary Surface
          subtle: '#EFECE2',      // Slightly darker warm accent
          border: '#E5E0D3',      // Soft warm border
          borderGold: 'rgba(201, 162, 39, 0.18)',
          emerald: '#063B32',     // Deep Emerald
          darkEmerald: '#042C26', // Darker Emerald
          lightEmerald: '#0B5145',// Soft Emerald
          gold: '#C9A227',        // Champagne Gold
          softGold: '#E2C766',    // Soft Gold
          lightGold: '#FAF4DC',   // Pale Gold Pill bg
          charcoal: '#18211F',    // Primary text
          muted: '#69736F',       // Secondary muted text
          success: '#0E9F6E',     // Success green
          warning: '#C88A16',     // Warning amber/gold
          danger: '#C94B4B',      // Danger red
        },
        emerald: {
          50: '#F0F9F6',
          100: '#E0F3EE',
          200: '#C1E7DC',
          300: '#8DCFBF',
          400: '#4EB19D',
          500: '#0E9F6E',
          600: '#063B32',
          700: '#042C26',
          800: '#03201C',
          900: '#021613',
          950: '#010D0B',
        },
        gold: {
          50: '#FDFBF0',
          100: '#FAF4DC',
          200: '#F4E7B4',
          300: '#EBD684',
          400: '#E2C766',
          500: '#C9A227',
          600: '#B08B1F',
          700: '#8C6C16',
          800: '#684F11',
          900: '#48360B',
        },
      },
      fontFamily: {
        sans: ['Manrope', 'DM Sans', 'Inter', 'system-ui', 'sans-serif'],
        heading: ['DM Sans', 'Manrope', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'wealth-card': '0 1px 3px 0 rgba(24, 33, 31, 0.04), 0 1px 2px -1px rgba(24, 33, 31, 0.04)',
        'wealth-elevated': '0 8px 30px -4px rgba(24, 33, 31, 0.06), 0 4px 12px -2px rgba(24, 33, 31, 0.03)',
        'wealth-gold': '0 0 25px -4px rgba(201, 162, 39, 0.28)',
        'wealth-emerald': '0 8px 24px -4px rgba(6, 59, 50, 0.35)',
      }
    },
  },
  plugins: [],
}

