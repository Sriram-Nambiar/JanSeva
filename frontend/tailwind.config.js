/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        charcoal: "#171e19",
        "dark-gray": "#272727",
        gold: "#ffe17c",
        sage: "#b7c6c2",
      },
      fontFamily: {
        anton: ['"Anton"', 'sans-serif'],
        satoshi: ['"Satoshi"', '"Plus Jakarta Sans"', 'sans-serif'],
        sans: ['"Satoshi"', '"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"Space Mono"', 'monospace'],
      },
      backgroundImage: {
        'grid-pattern': 'linear-gradient(to right, rgba(183, 198, 194, 0.25) 1px, transparent 1px), linear-gradient(to bottom, rgba(183, 198, 194, 0.25) 1px, transparent 1px)',
      },
      backgroundSize: {
        'grid-pattern': '40px 40px',
      },
      transitionTimingFunction: {
        'smooth-bounce': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [],
}
