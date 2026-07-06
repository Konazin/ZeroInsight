/**
 * Tema Midnight Purple — espelha a paleta do frontend desktop
 * (frontend/src/styles/globals.css) para consistência visual entre plataformas.
 */
export const colors = {
  bgBase: "#0D0B1A",
  bgSurface: "#15122A",
  bgElevated: "#1C1830",
  bgOverlay: "#100D22",
  bgInput: "#191630",

  border: "#2A2347",
  borderSubtle: "#1E1B38",

  textPrimary: "#F5F3FF",
  textMuted: "#B8B2D9",
  textSubtle: "#6B6494",

  accent: "#7C3AED",
  accentHover: "#6D28D9",
  accentLight: "#A78BFA",
  accentBg: "#1E1540",

  success: "#22C55E",
  warning: "#F59E0B",
  danger: "#EF4444",
} as const;

export const radius = {
  sm: 8,
  md: 10,
  lg: 14,
  xl: 16,
  pill: 999,
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
} as const;

export const font = {
  h1: 22,
  h2: 18,
  h3: 15,
  body: 14,
  small: 12,
  tiny: 11,
} as const;

export type ThemeColors = typeof colors;
