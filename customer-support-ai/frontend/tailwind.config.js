/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./hooks/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "system-ui", "sans-serif"],
      },
      colors: {
        surface: {
          900: "#0A0C14",
          800: "#0F1117",
          700: "#1A1D27",
          600: "#1E2130",
          500: "#2A2D3A",
        },
        brand: {
          DEFAULT: "#6366F1",
          hover: "#5558E3",
          light: "#6366F115",
        },
        agent: {
          billing:   "#6366F1",
          technical: "#10B981",
          product:   "#F59E0B",
          complaint: "#EF4444",
          faq:       "#8B5CF6",
        },
      },
      animation: {
        bounce: "bounce 1.2s ease-in-out infinite",
        pulse:  "pulse 1.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
