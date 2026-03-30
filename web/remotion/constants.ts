export const VIDEO_FPS = 30;
export const VIDEO_WIDTH = 1280;
export const VIDEO_HEIGHT = 720;

// Hero preview: ~11 seconds
export const HERO_DURATION = 330;
export const HERO_FPS = VIDEO_FPS;
export const HERO_WIDTH = VIDEO_WIDTH;
export const HERO_HEIGHT = VIDEO_HEIGHT;

// Feature preview: ~19 seconds
export const FEATURE_DURATION = 570;

// Design tokens — extracted from globals.css oklch values
export const COLORS = {
  background: "#fafaf8",
  foreground: "#0f172a",
  card: "#ffffff",
  primary: "#047857",
  primaryLight: "#d1fae5",
  secondary: "#f0f5f0",
  accent: "#059669",
  accentLight: "#a7f3d0",
  border: "#dde5dd",
  muted: "#ecf1ec",
  mutedForeground: "#64748b",
  // Extended palette
  darkPrimary: "#022c22",
  warmWhite: "#f8faf8",
  emerald400: "#34d399",
  amber500: "#f59e0b",
  blue500: "#3b82f6",
  violet500: "#8b5cf6",
  red500: "#ef4444",
  cyan500: "#06b6d4",
} as const;

// Font families — from layout.tsx: Inter + Geist Mono
export const FONTS = {
  heading: "'Inter', system-ui, sans-serif",
  body: "'Inter', system-ui, sans-serif",
  mono: "'Geist Mono', 'SF Mono', monospace",
} as const;

// Hero scenes (330 frames total)
export const HERO_SCENES = {
  title: { from: 0, duration: 110 },
  valueProps: { from: 95, duration: 130 },
  network: { from: 210, duration: 120 },
} as const;

// Feature preview scenes (570 frames total)
export const FEATURE_SCENES = {
  intro: { from: 0, duration: 80 },
  architecture: { from: 65, duration: 135 },
  safety: { from: 185, duration: 145 },
  phases: { from: 315, duration: 125 },
  outro: { from: 425, duration: 145 },
} as const;
