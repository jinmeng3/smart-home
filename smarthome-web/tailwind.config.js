/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      boxShadow: {
        soft: '0 18px 48px rgba(33, 77, 142, 0.08)',
      },
    },
  },
  plugins: [],
}
