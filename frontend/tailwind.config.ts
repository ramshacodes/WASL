import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#070B14",
          900: "#0B1220",
          800: "#111A2E",
          700: "#1A253C",
          600: "#26324C",
        },
        sand: {
          300: "#E6D9B8",
          400: "#D8C9A3",
          500: "#C9B48A",
        },
        gold: {
          300: "#E3C878",
          400: "#D4B25C",
          500: "#C9A227",
        },
        ivory: "#F5F3EC",
        mute: "#8B93A6",
        success: "#6FCF97",
        danger: "#D6604D",
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        body: ["var(--font-inter)", "system-ui", "sans-serif"],
        arabic: ["var(--font-arabic)", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 20px 40px -20px rgba(0,0,0,0.6)",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
        signal: {
          "0%": { transform: "scaleX(0)", opacity: "0.4" },
          "100%": { transform: "scaleX(1)", opacity: "1" },
        },
      },
      animation: {
        fadeUp: "fadeUp 0.35s ease-out both",
        pulseDot: "pulseDot 1.6s ease-in-out infinite",
        signal: "signal 1.1s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
