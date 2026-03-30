import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, FONTS } from "../constants";

export const IntroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lineExpand = spring({
    frame,
    fps,
    config: { damping: 200, stiffness: 60 },
    delay: 5,
  });

  const titleEntrance = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 80 },
    delay: 10,
  });

  const subtitleOpacity = interpolate(frame, [30, 50], [0, 0.7], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const fadeOut = interpolate(frame, [60, 80], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.background,
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeOut,
      }}
    >
      {/* Expanding accent line */}
      <div
        style={{
          position: "absolute",
          top: "42%",
          left: "50%",
          transform: "translateX(-50%)",
          height: 2,
          width: interpolate(lineExpand, [0, 1], [0, 200]),
          backgroundColor: COLORS.accent,
          borderRadius: 1,
        }}
      />

      {/* Title */}
      <div
        style={{
          fontFamily: FONTS.heading,
          fontSize: 56,
          fontWeight: 700,
          color: COLORS.foreground,
          transform: `translateY(${interpolate(titleEntrance, [0, 1], [20, 0])}px)`,
          opacity: interpolate(titleEntrance, [0, 1], [0, 1]),
          letterSpacing: "-0.03em",
        }}
      >
        AI Health Coach
      </div>

      {/* Subtitle */}
      <div
        style={{
          position: "absolute",
          top: "58%",
          fontFamily: FONTS.body,
          fontSize: 18,
          color: COLORS.mutedForeground,
          opacity: subtitleOpacity,
        }}
      >
        Architecture & Design
      </div>
    </AbsoluteFill>
  );
};
