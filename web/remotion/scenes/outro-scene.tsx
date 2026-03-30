import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, FONTS } from "../constants";

const PROOF_POINTS = [
  { number: "701", label: "tests passing", color: COLORS.accent },
  { number: "113", label: "adversarial prompts", color: COLORS.red500 },
  { number: "< 1%", label: "safety false-negative rate", color: COLORS.primary },
];

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Closing accent line
  const lineExpand = spring({
    frame,
    fps,
    config: { damping: 200, stiffness: 60 },
    delay: 90,
  });

  const closingIn = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 60 },
    delay: 100,
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.background,
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeIn,
      }}
    >
      {/* Proof points */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 24,
        }}
      >
        {PROOF_POINTS.map((point, i) => {
          const entrance = spring({
            frame,
            fps,
            config: { damping: 14, stiffness: 80 },
            delay: 10 + i * 14,
          });
          const translateY = interpolate(entrance, [0, 1], [20, 0]);
          const opacity = interpolate(entrance, [0, 1], [0, 1]);

          return (
            <div
              key={point.label}
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 10,
                opacity,
                transform: `translateY(${translateY}px)`,
              }}
            >
              <span
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 36,
                  fontWeight: 700,
                  color: point.color,
                  lineHeight: 1,
                }}
              >
                {point.number}
              </span>
              <span
                style={{
                  fontFamily: FONTS.body,
                  fontSize: 16,
                  color: COLORS.mutedForeground,
                }}
              >
                {point.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Closing accent line */}
      <div
        style={{
          position: "absolute",
          bottom: 160,
          left: "50%",
          transform: "translateX(-50%)",
          height: 2,
          width: interpolate(lineExpand, [0, 1], [0, 160]),
          backgroundColor: COLORS.accent,
          borderRadius: 1,
        }}
      />

      {/* Closing text */}
      <div
        style={{
          position: "absolute",
          bottom: 125,
          fontFamily: FONTS.body,
          fontSize: 14,
          color: COLORS.mutedForeground,
          opacity: interpolate(closingIn, [0, 1], [0, 0.7]),
        }}
      >
        Safety-first by design
      </div>
    </AbsoluteFill>
  );
};
