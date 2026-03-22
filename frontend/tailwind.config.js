/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'space-cyan': '#44A194',
        'space-purple': '#537D96',
        'space-bg': '#1a1917',
        'space-surface': '#242220',
        'space-input': '#2e2b28',
        'space-pale': '#537D96',
        'space-lavender': '#F4F0E4',
        'space-pink': '#EC8F8D',
      },
    },
  },
  plugins: [],
}