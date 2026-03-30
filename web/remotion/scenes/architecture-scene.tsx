import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, FONTS } from "../constants";

/**
 * Tool Calling Scene — shows a user message triggering autonomous
 * tool execution (set_goal), demonstrating phase-bound tool calling.
 */
export const ArchitectureScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [115, 135], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const s = (delay: number) =>
    spring({ frame, fps, config: { damping: 14, stiffness: 80 }, delay });

  const labelIn = s(5);
  const userMsgIn = s(10);
  const thinkingIn = s(28);
  const toolCallIn = s(42);
  const toolResultIn = s(58);
  const coachMsgIn = s(72);

  // Thinking dots animation
  const dotPhase = (frame - 28) * 0.15;
  const dot1 = Math.sin(dotPhase) * 0.4 + 0.6;
  const dot2 = Math.sin(dotPhase + 1) * 0.4 + 0.6;
  const dot3 = Math.sin(dotPhase + 2) * 0.4 + 0.6;
  const showThinking = frame >= 28 && frame < 42;

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
          top: 110,
          fontFamily: FONTS.body,
          fontSize: 13,
          fontWeight: 600,
          color: COLORS.accent,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          opacity: interpolate(labelIn, [0, 1], [0, 1]),
        }}
      >
        Autonomous Tool Calling
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          width: 520,
          gap: 14,
        }}
      >
        {/* User message */}
        <div
          style={{
            alignSelf: "flex-end",
            opacity: interpolate(userMsgIn, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(userMsgIn, [0, 1], [12, 0])}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: COLORS.primary,
              borderRadius: "16px 16px 4px 16px",
              padding: "10px 16px",
              maxWidth: 320,
            }}
          >
            <div
              style={{
                fontFamily: FONTS.body,
                fontSize: 13,
                color: "#fff",
                lineHeight: 1.5,
              }}
            >
              I want to walk 30 minutes, 3 times a week
            </div>
          </div>
          <div
            style={{
              fontFamily: FONTS.body,
              fontSize: 10,
              color: COLORS.mutedForeground,
              textAlign: "right" as const,
              marginTop: 3,
            }}
          >
            Patient
          </div>
        </div>

        {/* Thinking indicator */}
        {showThinking && (
          <div style={{ alignSelf: "flex-start", paddingLeft: 4 }}>
            <div
              style={{
                display: "flex",
                gap: 4,
                padding: "10px 16px",
                backgroundColor: COLORS.card,
                border: `1px solid ${COLORS.border}`,
                borderRadius: "16px 16px 16px 4px",
              }}
            >
              {[dot1, dot2, dot3].map((opacity, i) => (
                <div
                  key={i}
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    backgroundColor: COLORS.mutedForeground,
                    opacity,
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Tool call */}
        <div
          style={{
            alignSelf: "center",
            opacity: interpolate(toolCallIn, [0, 1], [0, 1]),
            transform: `scale(${interpolate(toolCallIn, [0, 1], [0.9, 1])})`,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              backgroundColor: "#f5f3ff",
              border: "1px solid #e9e5ff",
              borderRadius: 10,
              padding: "8px 16px",
            }}
          >
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                backgroundColor: COLORS.violet500,
              }}
            />
            <span
              style={{
                fontFamily: FONTS.mono,
                fontSize: 12,
                color: COLORS.violet500,
                fontWeight: 500,
              }}
            >
              set_goal
            </span>
            <span
              style={{
                fontFamily: FONTS.mono,
                fontSize: 11,
                color: COLORS.mutedForeground,
              }}
            >
              (&quot;Walk 30 min, 3x/week&quot;)
            </span>
          </div>
        </div>

        {/* Tool result */}
        <div
          style={{
            alignSelf: "center",
            opacity: interpolate(toolResultIn, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(toolResultIn, [0, 1], [8, 0])}px)`,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "5px 12px",
              borderRadius: 8,
              backgroundColor: "#f0fdf4",
              border: "1px solid #bbf7d0",
            }}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <circle cx="6" cy="6" r="6" fill={COLORS.accent} />
              <path
                d="M3.5 6L5.5 8L8.5 4.5"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span
              style={{
                fontFamily: FONTS.mono,
                fontSize: 11,
                color: COLORS.accent,
              }}
            >
              Goal created with 4-week milestones
            </span>
          </div>
        </div>

        {/* Coach response */}
        <div
          style={{
            alignSelf: "flex-start",
            opacity: interpolate(coachMsgIn, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(coachMsgIn, [0, 1], [12, 0])}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: COLORS.card,
              border: `1px solid ${COLORS.border}`,
              borderRadius: "16px 16px 16px 4px",
              padding: "10px 16px",
              maxWidth: 380,
              boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
            }}
          >
            <div
              style={{
                fontFamily: FONTS.body,
                fontSize: 13,
                color: COLORS.foreground,
                lineHeight: 1.5,
              }}
            >
              I&apos;ve set that as your goal! Walking 30 minutes, 3 times a
              week is a great target. I&apos;ve created weekly milestones to
              help you build up gradually.
            </div>
          </div>
          <div
            style={{
              fontFamily: FONTS.body,
              fontSize: 10,
              color: COLORS.mutedForeground,
              marginTop: 3,
            }}
          >
            Health Coach
          </div>
        </div>
      </div>

      {/* Phase badge */}
      <div
        style={{
          position: "absolute",
          bottom: 130,
          display: "flex",
          alignItems: "center",
          gap: 16,
          opacity: interpolate(coachMsgIn, [0, 1], [0, 0.6]),
        }}
      >
        <span
          style={{
            fontFamily: FONTS.body,
            fontSize: 11,
            color: COLORS.mutedForeground,
          }}
        >
          Phase: ONBOARDING
        </span>
        <span
          style={{
            width: 1,
            height: 12,
            backgroundColor: COLORS.border,
            display: "inline-block",
          }}
        />
        <span
          style={{
            fontFamily: FONTS.body,
            fontSize: 11,
            color: COLORS.mutedForeground,
          }}
        >
          Available tools: set_goal
        </span>
      </div>
    </AbsoluteFill>
  );
};
