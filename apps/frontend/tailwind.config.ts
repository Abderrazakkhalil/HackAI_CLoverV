import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Matte charcoal depth stack
        charcoal: {
          950: "#070707",
          900: "#0b0b0d",
          850: "#101012",
          800: "#151517",
          750: "#1b1b1f",
          700: "#232328",
          600: "#c9b89a",
        },
        // Warm gold / bronze accent system
        gold: {
          50: "#fbf3e1",
          200: "#ecd6a3",
          300: "#e3c483",
          400: "#d9b46c",
          DEFAULT: "#d4a85a",
          500: "#d4a85a",
          600: "#bb8f43",
          700: "#9a7332",
          bronze: "#8a6a3a",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        "gold-sm": "0 0 0 1px rgba(212,168,90,0.22)",
        gold: "0 0 0 1px rgba(212,168,90,0.28), 0 18px 50px -20px rgba(212,168,90,0.40)",
        "gold-lg":
          "0 0 0 1px rgba(212,168,90,0.30), 0 30px 80px -28px rgba(212,168,90,0.55)",
        card: "0 40px 90px -40px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255,255,255,0.04)",
      },
      backgroundImage: {
        "gold-gradient":
          "linear-gradient(135deg, #e3c483 0%, #d4a85a 45%, #9a7332 100%)",
        "gold-sheen":
          "linear-gradient(135deg, rgba(227,196,131,0.18), rgba(154,115,50,0.06))",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(0.9)", opacity: "0.65" },
          "70%": { transform: "scale(1.9)", opacity: "0" },
          "100%": { opacity: "0" },
        },
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        shimmer: { "100%": { transform: "translateX(100%)" } },
        "spin-slow": { to: { transform: "rotate(360deg)" } },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "pulse-ring": "pulse-ring 1.8s cubic-bezier(0.4,0,0.6,1) infinite",
        float: "float 5s ease-in-out infinite",
        shimmer: "shimmer 1.6s infinite",
        "spin-slow": "spin-slow 9s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
