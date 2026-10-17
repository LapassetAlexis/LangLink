/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Palette « éditorial chaleureux » : ambre/sable plutôt que bleu générique.
        brand: {
          50: '#fdf6e9',
          100: '#f9e9c9',
          200: '#f3d69a',
          300: '#f0c274',
          400: '#f0b357',
          500: '#e09b3d',
          600: '#c9862f',
          700: '#a86c24',
          800: '#7c4f1c',
          900: '#553615',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Fraunces', 'Georgia', 'serif'],
      },
      borderRadius: {
        '4xl': '2rem',
      },
    },
  },
  plugins: [],
}
