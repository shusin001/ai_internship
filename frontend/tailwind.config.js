/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#ecfdf5',
          100: '#d1fae5',
          600: '#0f766e',
          700: '#115e59'
        },
        accent: {
          50: '#fff7ed',
          100: '#ffedd5',
          600: '#c2410c',
          700: '#9a3412'
        }
      },
      boxShadow: {
        soft: '0 12px 28px -18px rgba(12, 74, 110, 0.28)'
      }
    }
  },
  plugins: []
};
