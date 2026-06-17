/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-medis': '#1B262C',    // Navy Gelap
        'primary-medis': '#0F4C75', // Biru Utama
        'secondary-medis': '#3282B8', // Biru Muda
        'light-medis': '#BBE1FA',     // Biru Pucat Background
      },
    },
  },
  plugins: [],
};
