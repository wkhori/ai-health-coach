import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, FONTS } from "../constants";

const PHASES = [
  { name: "PENDING", color: COLORS.mutedForeground },
  { name: "ONBOARDING", color: COLORS.blue500 },
  { name: "ACTIVE", color: COLORS.accent },
  { name: "RE_ENGAGING", color: COLORS.amber500 },
  { name: "DORMANT", color: COLORS.red500 },
];

const TRANSITIONS = [
  "consent given",
  "goal confirmed",
  "48h inactive",
  "3 attempts, no response",
];

export const PhasesScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [105, 125], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const labelIn = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 60 },
    delay: 5,
  });

  // Highlight that moves through phases
  const highlightProgress = interpolate(frame, [45, 95], [0, 4], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const activePhaseIndex = Math.min(Math.floor(highlightProgress), 4);

  const footnoteIn = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 60 },
    delay: 85,
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.background,
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeIn * fadeOut,
      }}
    >
      {/* Section label */}
      <div
        style={{
          position: "absolute",
          top: 150,
          fontFamily: FONTS.body,
          fontSize: 13,
          fontWeight: 600,
          color: COLORS.accent,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          opacity: interpolate(labelIn, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(labelIn, [0, 1], [10, 0])}px)`,
        }}
      >
        Deterministic Phase Routing
      </div>

      {/* Phase chain */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 0,
        }}
      >
        {PHASES.map((phase, i) => {
          const phaseEntrance = spring({
            frame,
            fps,
            config: { damping: 14, stiffness: 80 },
            delay: 10 + i * 6,
          });
          const isActive = i <= activePhaseIndex && frame >= 45;
          const isCurrentHighlight = i === activePhaseIndex && frame >= 45;

          return (
            <div
              key={phase.name}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 0,
              }}
            >
              {/* Phase pill */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  opacity: interpolate(phaseEntrance, [0, 1], [0, 1]),
                  transform: `translateY(${interpolate(phaseEntrance, [0, 1], [15, 0])}px)`,
                }}
              >
                <div
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 11,
                    fontWeight: 600,
                    color: isActive ? "#fff" : phase.color,
                    backgroundColor: isActive ? phase.color : COLORS.card,
                    border: `1.5px solid ${isActive ? phase.color : COLORS.border}`,
                    borderRadius: 10,
                    padding: "8px 14px",
                    transition: "all 0.3s",
                    boxShadow: isCurrentHighlight
                      ? `0 0 16px ${phase.color}40`
                      : "0 1px 4px rgba(0,0,0,0.04)",
                    whiteSpace: "nowrap" as const,
                  }}
                >
                  {phase.name}
                </div>
              </div>

              {/* Arrow + transition label */}
              {i < PHASES.length - 1 && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    margin: "0 4px",
                    opacity: interpolate(
                      spring({
                        frame,
                        fps,
                        config: { damping: 20, stiffness: 60 },
                        delay: 14 + i * 6,
                      }),
                      [0, 1],
                      [0, 1]
                    ),
                  }}
                >
                  <span
                    style={{
                      fontFamily: FONTS.body,
                      fontSize: 9,
                      color: COLORS.mutedForeground,
                      marginBottom: 3,
                      whiteSpace: "nowrap" as const,
                    }}
                  >
                    {TRANSITIONS[i]}
                  </span>
                  <span
                    style={{
                      fontSize: 12,
                      color: COLORS.mutedForeground,
                    }}
                  >
                    &rarr;
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footnote */}
      <div
        style={{
          position: "absolute",
          bottom: 170,
          fontFamily: FONTS.body,
          fontSize: 13,
          color: COLORS.mutedForeground,
          opacity: interpolate(footnoteIn, [0, 1], [0, 0.8]),
          transform: `translateY(${interpolate(footnoteIn, [0, 1], [8, 0])}px)`,
        }}
      >
        100% application code &middot; No LLM routing decisions
      </div>
    </AbsoluteFill>
  );
};
