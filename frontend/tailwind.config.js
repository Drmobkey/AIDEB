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
        'dark-medis': '#0A2E2A',      // Deep Teal Gelap untuk teks kontras tinggi
        'primary-medis': '#0A7C6E',   // Warna Dasar Teal Utama AIDEB
        'secondary-medis': '#14B8A6', // Tosca Terang untuk aksen gradasi
        'light-medis': '#F0FDFA',     // Teal Pucat untuk latar belakang & glow
      },
    },
  },
  plugins: [],
};
