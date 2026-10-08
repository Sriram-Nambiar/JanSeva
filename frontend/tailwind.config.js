/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ground: "#EFEFEE",
        stage: "#E4E4E2",
        ink: "#0D0D0F",
        "ink-secondary": "#43444A",
        muted: "#6E6F76",
        accent: "#2F5BFF",
        "accent-light": "#7C97FF",
      },
      fontFamily: {
        display: ['"Archivo"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      letterSpacing: {
        tightest: '-0.055em',
        tighter: '-0.04em',
        widest: '0.16em',
        wide: '0.14em',
      },
      lineHeight: {
        display: '0.74',
        tight: '0.88',
      },
      borderRadius: {
        none: '0',
        DEFAULT: '0',
        sm: '0',
        md: '0',
        lg: '0',
        xl: '0',
        '2xl': '0',
        '3xl': '0',
        full: '9999px',
      },
      transitionTimingFunction: {
        snappy: 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
}
