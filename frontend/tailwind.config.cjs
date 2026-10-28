// tailwind.config.cjs
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx,html}'],
  theme: {
    extend: {
      colors: {
        primary: 'hsl(210, 50%, 55%)',
        accent: 'hsl(160, 45%, 52%)',
        danger: 'hsl(0, 70%, 55%)',
        neutral: 'hsl(220, 10%, 20%)',
      },
    },
  },
  plugins: [],
};
