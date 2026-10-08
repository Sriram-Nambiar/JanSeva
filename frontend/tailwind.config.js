/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: "#FDFCF8",
        sage: "#E8EFE8",
        lavender: "#EFEDF4",
        coral: "#FFB7B2",
        "soft-black": "#292524",
        "soft-muted": "#78716C",
        "blob-peach": "#FFE4E1",
        "blob-lavender": "#E6E6FA",
      },
      fontFamily: {
        outfit: ['"Outfit"', 'sans-serif'],
        reenie: ['"Reenie Beanie"', 'cursive'],
      },
      borderRadius: {
        '2xl': '1.5rem',
        '3xl': '2rem',
        '4xl': '2.5rem',
        '5xl': '3rem',
        '6xl': '4rem',
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        'soft-lg': '0 10px 30px -3px rgba(0, 0, 0, 0.06)',
        'coral-glow': '0 8px 28px -4px rgba(255, 183, 178, 0.45)',
      },
      animation: {
        'float-slow': 'float 6s ease-in-out infinite',
        'float-reverse': 'float-rev 7s ease-in-out infinite',
        'breathe': 'breathe 4s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        'float-rev': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(12px)' },
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)', boxShadow: '0 0 0 0 rgba(255, 183, 178, 0.4)' },
          '50%': { transform: 'scale(1.06)', boxShadow: '0 0 24px 8px rgba(255, 183, 178, 0.35)' },
        },
      },
    },
  },
  plugins: [],
}
