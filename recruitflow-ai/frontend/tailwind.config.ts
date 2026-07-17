import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17202a",
        muted: "#64748b",
        line: "#d9e2ec",
        panel: "#f8fafc",
        brand: "#1f6feb",
        success: "#247a4d",
        warning: "#b7791f",
        danger: "#b42318"
      }
    }
  },
  plugins: []
};

export default config;
