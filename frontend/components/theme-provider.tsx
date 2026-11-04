"use client";

import * as React from "react";

const THEME_KEY = "edumind-theme";

export type Theme = "light" | "dark" | "system";

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
}

export function ThemeProvider({
  children,
  defaultTheme = "system",
  storageKey = THEME_KEY,
}: ThemeProviderProps) {
  const [theme, setTheme] = React.useState<Theme>(defaultTheme);
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(storageKey) as Theme | null;
      if (stored) setTheme(stored);
      applyTheme(document.documentElement, stored || defaultTheme);
    }
  }, []);

  const applyTheme = (el: HTMLElement, t: Theme) => {
    let resolved = t;
    if (t === "system") {
      resolved = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    if (resolved === "dark") el.classList.add("dark");
    else el.classList.remove("dark");
  };

  const toggle = (next: Theme) => {
    setTheme(next);
    if (typeof window !== "undefined") {
      localStorage.setItem(storageKey, next);
      applyTheme(document.documentElement, next);
    }
  };

  return (
    <ThemeContext.Provider value={{ theme, toggle, mounted }}>
      {children}
    </ThemeContext.Provider>
  );
}

const ThemeContext = React.createContext<{
  theme: Theme;
  toggle: (t: Theme) => void;
  mounted: boolean;
}>({ theme: "system", toggle: () => {}, mounted: false });

export function useTheme() {
  return React.useContext(ThemeContext);
}
