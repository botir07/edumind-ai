module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: "#0f172a", light: "#1e293b" },
        blue: { DEFAULT: "#2563eb", light: "#3b82f6" },
        violet: { DEFAULT: "#7c3aed", light: "#8b5cf6" },
        neutral: { DEFAULT: "#f8fafc", dark: "#334155" },
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}
