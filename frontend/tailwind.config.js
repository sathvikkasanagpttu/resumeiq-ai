/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          500: '#0d9488',
          600: '#0f766e',
          700: '#115e59',
          900: '#134e4a',
        },
        slate: {
          850: '#151f30',
          950: '#0a0f1d'
        }
      }
    },
  },
  plugins: [],
}
