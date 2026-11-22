// Tokeny z planu sprintu finalowego (par. 9): jasny motyw instytucjonalny.
import { createTheme } from "@mantine/core";

export const TOKENS = {
  bg: "#F5F6F8",
  surface: "#FFFFFF",
  text: "#1A1F2B",
  muted: "#5B6472",
  border: "#DDE1E6",
  accent: "#0B3D91",
  risk: { high: "#B42318", medium: "#B54708", low: "#475467" },
};

// Skala granatu wokol #0B3D91 (indeks 7 = akcent).
const navy = ["#eef3fb", "#d7e2f4", "#adc3e8", "#7f9fda", "#5880ce", "#3c69c3", "#1d4fa8", "#0B3D91", "#08306f", "#05224f"];

export const theme = createTheme({
  primaryColor: "navy",
  primaryShade: 7,
  colors: { navy },
  black: TOKENS.text,
  fontFamily: "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
  fontFamilyMonospace: "'JetBrains Mono', ui-monospace, Consolas, monospace",
  fontSizes: { xs: "12px", sm: "13px", md: "14px", lg: "16px", xl: "18px" },
  defaultRadius: "xs",
  radius: { xs: "4px", sm: "4px", md: "4px", lg: "6px", xl: "8px" },
  shadows: { xs: "none", sm: "none", md: "0 8px 24px rgba(26, 31, 43, 0.12)" },
  headings: {
    fontWeight: "600",
    sizes: { h1: { fontSize: "20px" }, h2: { fontSize: "18px" }, h3: { fontSize: "16px" }, h4: { fontSize: "14px" } },
  },
  components: {
    Paper: { defaultProps: { withBorder: true, radius: "xs", shadow: "xs" } },
    Button: { defaultProps: { radius: "xs", size: "sm" } },
    Badge: { defaultProps: { radius: "xs", variant: "light" } },
  },
});

export const RISK_LABEL = { high: "Wysokie", medium: "Średnie", low: "Niskie" };
