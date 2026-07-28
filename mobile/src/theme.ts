/** Sistema visual monocromático compartilhado com o app desktop. */
export const colors = {
  bgBase: "#070707",
  bgSurface: "#101010",
  bgElevated: "#191919",
  bgOverlay: "#0B0B0B",
  bgInput: "#0D0D0D",

  border: "#343434",
  borderSubtle: "#232323",

  textPrimary: "#FAFAFA",
  textMuted: "#B5B5B5",
  textSubtle: "#777777",

  accent: "#FFFFFF",
  accentHover: "#E6E6E6",
  accentLight: "#FFFFFF",
  accentBg: "#222222",

  success: "#FFFFFF",
  warning: "#BDBDBD",
  danger: "#FFFFFF",
} as const;

export const radius = {
  sm: 10,
  md: 12,
  lg: 16,
  xl: 20,
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
  h1: 28,
  h2: 20,
  h3: 16,
  body: 15,
  small: 13,
  tiny: 11,
} as const;

export type ThemeColors = typeof colors;
