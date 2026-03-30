import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, FONTS } from "../constants";

export const SafetyScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [125, 145], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const s = (delay: number) =>
    spring({ frame, fps, config: { damping: 14, stiffness: 80 }, delay });

  const labelIn = s(5);
  const messageIn = s(12);
  const arrow1 = s(22);
  const tier1In = s(28);
  const arrow2 = s(40);
  const tier2In = s(46);
  const outcomesIn = s(60);
  const crisisIn = s(80);

  // Animated arrow line
  const arrowLine = (progress: number) =>
    interpolate(progress, [0, 1], [0, 40]);

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
          top: 130,
          fontFamily: FONTS.body,
          fontSize: 13,
          fontWeight: 600,
          color: COLORS.accent,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          opacity: interpolate(labelIn, [0, 1], [0, 1]),
        }}
      >
        Two-Tier Safety Classifier
      </div>

      {/* Main pipeline flow */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 0,
        }}
      >
        {/* Patient message */}
        <div
          style={{
            opacity: interpolate(messageIn, [0, 1], [0, 1]),
            transform: `translateX(${interpolate(messageIn, [0, 1], [-20, 0])}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: COLORS.card,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 12,
              padding: "12px 16px",
              maxWidth: 140,
              boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
            }}
          >
            <div
              style={{
                fontFamily: FONTS.body,
                fontSize: 10,
                fontWeight: 600,
                color: COLORS.mutedForeground,
                marginBottom: 4,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              Patient Message
            </div>
            <div
              style={{
                fontFamily: FONTS.body,
                fontSize: 12,
                color: COLORS.foreground,
                lineHeight: 1.4,
              }}
            >
              &ldquo;I want to walk more this week&rdquo;
            </div>
          </div>
        </div>

        {/* Arrow 1 */}
        <div
          style={{
            width: arrowLine(arrow1),
            height: 1,
            backgroundColor: COLORS.border,
            margin: "0 4px",
          }}
        />

        {/* Tier 1 */}
        <div
          style={{
            opacity: interpolate(tier1In, [0, 1], [0, 1]),
            transform: `scale(${interpolate(tier1In, [0, 1], [0.9, 1])})`,
          }}
        >
          <div
            style={{
              backgroundColor: COLORS.card,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 12,
              padding: "14px 18px",
              textAlign: "center" as const,
              boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
            }}
          >
            <div
              style={{
                fontFamily: FONTS.body,
                fontSize: 14,
                fontWeight: 600,
                color: COLORS.foreground,
              }}
            >
              Tier 1
            </div>
            <div
              style={{
                fontFamily: FONTS.body,
                fontSize: 11,
                color: COLORS.mutedForeground,
                marginTop: 2,
              }}
            >
              Regex Pre-filter
            </div>
            <div
              style={{
                fontFamily: FONTS.mono,
                fontSize: 10,
                color: COLORS.accent,
                marginTop: 6,
                backgroundColor: COLORS.primaryLight,
                borderRadius: 10,
                padding: "2px 10px",
                display: "inline-block",
              }}
            >
              &lt; 1ms
            </div>
          </div>
        </div>

        {/* Arrow 2 */}
        <div
          style={{
            width: arrowLine(arrow2),
            height: 1,
            backgroundColor: COLORS.border,
            margin: "0 4px",
          }}
        />

        {/* Tier 2 */}
        <div
          style={{
            opacity: interpolate(tier2In, [0, 1], [0, 1]),
            transform: `scale(${interpolate(tier2In, [0, 1], [0.9, 1])})`,
          }}
        >
          <div
            style={{
              backgroundColor: COLORS.card,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 12,
              padding: "14px 18px",
              textAlign: "center" as const,
              boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
            }}
          >
            <div
              style={{
                fontFamily: FONTS.body,
                fontSize: 14,
                fontWeight: 600,
                color: COLORS.foreground,
              }}
            >
              Tier 2
            </div>
            <div
              style={{
                fontFamily: FONTS.body,
                fontSize: 11,
                color: COLORS.mutedForeground,
                marginTop: 2,
              }}
            >
              LLM Classifier
            </div>
            <div
              style={{
                fontFamily: FONTS.mono,
                fontSize: 10,
                color: COLORS.violet500,
                marginTop: 6,
                backgroundColor: "#f5f3ff",
                borderRadius: 10,
                padding: "2px 10px",
                display: "inline-block",
              }}
            >
              ~200ms
            </div>
          </div>
        </div>

        {/* Arrow 3 */}
        <div
          style={{
            width: arrowLine(outcomesIn),
            height: 1,
            backgroundColor: COLORS.border,
            margin: "0 4px",
          }}
        />

        {/* Outcomes */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 6,
            opacity: interpolate(outcomesIn, [0, 1], [0, 1]),
            transform: `translateX(${interpolate(outcomesIn, [0, 1], [15, 0])}px)`,
          }}
        >
          {[
            { label: "SAFE", bg: "#f0fdf4", border: "#bbf7d0", color: COLORS.accent },
            { label: "REWRITE", bg: "#fffbeb", border: "#fde68a", color: COLORS.amber500 },
            { label: "BLOCK", bg: "#fef2f2", border: "#fecaca", color: COLORS.red500 },
          ].map((outcome) => (
            <div
              key={outcome.label}
              style={{
                fontFamily: FONTS.mono,
                fontSize: 11,
                fontWeight: 600,
                color: outcome.color,
                backgroundColor: outcome.bg,
                border: `1px solid ${outcome.border}`,
                borderRadius: 8,
                padding: "5px 14px",
                textAlign: "center" as const,
              }}
            >
              {outcome.label}
            </div>
          ))}
        </div>
      </div>

      {/* Crisis path */}
      <div
        style={{
          position: "absolute",
          bottom: 150,
          display: "flex",
          alignItems: "center",
          gap: 12,
          opacity: interpolate(crisisIn, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(crisisIn, [0, 1], [10, 0])}px)`,
        }}
      >
        <div
          style={{
            fontFamily: FONTS.mono,
            fontSize: 11,
            fontWeight: 600,
            color: COLORS.red500,
            backgroundColor: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: 8,
            padding: "5px 14px",
          }}
        >
          CRISIS
        </div>
        <span
          style={{
            fontSize: 11,
            color: COLORS.mutedForeground,
          }}
        >
          &rarr;
        </span>
        <div
          style={{
            fontFamily: FONTS.body,
            fontSize: 12,
            color: COLORS.foreground,
          }}
        >
          Hard-coded response &middot;{" "}
          <span style={{ color: COLORS.mutedForeground }}>
            988 Lifeline &middot; Never LLM-generated
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
