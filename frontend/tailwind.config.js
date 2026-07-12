/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./pages/**/*.html",
    "./src/ts/**/*.ts",
  ],
  theme: {
    extend: {
      colors: {
        voa: {
          50: "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
          950: "#0d3b3f",
        },
        ink: {
          900: "#0f1419",
          800: "#1a1f25",
          700: "#252b33",
          600: "#3a4250",
        },
        cream: {
          50: "#fefcf9",
          100: "#fef7ed",
          200: "#fdefd6",
        },
      },
      fontFamily: {
        display: ["'DM Serif Display'", "serif"],
        sans: ["'Inter'", "sans-serif"],
      },
      boxShadow: {
        premium: "0 10px 40px -10px rgba(13, 59, 63, 0.3)",
        card: "0 1px 3px rgba(0,0,0,0.04), 0 4px 20px rgba(0,0,0,0.04)",
        "card-hover": "0 8px 30px rgba(13, 59, 63, 0.12)",
        glow: "0 0 20px rgba(13, 148, 136, 0.15)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-in-left": {
          "0%": { opacity: "0", transform: "translateX(-20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.5s ease-out both",
        "fade-in": "fade-in 0.4s ease-out both",
        "slide-in-left": "slide-in-left 0.4s ease-out both",
        "scale-in": "scale-in 0.3s ease-out both",
      },
    },
  },
  plugins: [],
};
