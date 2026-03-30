import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import {
  COLORS,
  FONTS,
  HERO_SCENES,
  HERO_DURATION,
  HERO_FPS,
  HERO_WIDTH,
  HERO_HEIGHT,
} from "./constants";

export { HERO_DURATION, HERO_FPS, HERO_WIDTH, HERO_HEIGHT };

// ── Scene 1: Title Reveal ───────────────────────────────────────────
function TitleScene() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Word animations — slide in from opposite sides
  const words = ["AI", "Health", "Coach"];
  const directions = [-1, 1, -1];

  const lineExpand = spring({
    frame,
    fps,
    config: { damping: 200, stiffness: 60 },
    delay: 20,
  });

  const subtitleOpacity = interpolate(frame, [45, 65], [0, 0.7], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const fadeOut = interpolate(frame, [90, 110], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.darkPrimary,
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeOut,
      }}
    >
      <div
        style={{
          display: "flex",
          gap: 20,
          alignItems: "center",
        }}
      >
        {words.map((word, i) => {
          const entrance = spring({
            frame,
            fps,
            config: { damping: 14, stiffness: 80 },
            delay: i * 8,
          });
          const translateX = interpolate(
            entrance,
            [0, 1],
            [60 * directions[i], 0]
          );
          const opacity = interpolate(entrance, [0, 1], [0, 1]);

          return (
            <span
              key={word}
              style={{
                fontFamily: FONTS.heading,
                fontSize: 72,
                fontWeight: 700,
                color: i === 1 ? COLORS.emerald400 : "#ffffff",
                transform: `translateX(${translateX}px)`,
                opacity,
                letterSpacing: "-0.03em",
              }}
            >
              {word}
            </span>
          );
        })}
      </div>

      {/* Accent line */}
      <div
        style={{
          position: "absolute",
          top: "58%",
          left: "50%",
          transform: "translateX(-50%)",
          height: 2,
          width: interpolate(lineExpand, [0, 1], [0, 300]),
          backgroundColor: COLORS.accent,
          borderRadius: 1,
        }}
      />

      {/* Subtitle */}
      <div
        style={{
          position: "absolute",
          top: "64%",
          fontFamily: FONTS.body,
          fontSize: 20,
          color: COLORS.accentLight,
          opacity: subtitleOpacity,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        Wellness Coaching Platform
      </div>
    </AbsoluteFill>
  );
}

// ── Scene 2: Value Propositions ─────────────────────────────────────
function ValuePropsScene() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const props = [
    "AI-powered coaching for exercise adherence",
    "Every message passes through a safety classifier",
    "Proactive re-engagement when patients disengage",
  ];

  const fadeIn = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [110, 130], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
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
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 28,
          alignItems: "center",
          padding: "0 100px",
        }}
      >
        {props.map((text, i) => {
          const entrance = spring({
            frame,
            fps,
            config: { damping: 14, stiffness: 80 },
            delay: i * 12,
          });
          const translateY = interpolate(entrance, [0, 1], [30, 0]);
          const opacity = interpolate(entrance, [0, 1], [0, 1]);
          const isLast = i === props.length - 1;

          return (
            <div
              key={i}
              style={{
                fontFamily: FONTS.heading,
                fontSize: isLast ? 30 : 28,
                fontWeight: isLast ? 700 : 500,
                color: isLast ? COLORS.primary : COLORS.foreground,
                transform: `translateY(${translateY}px)`,
                opacity,
                textAlign: "center",
                lineHeight: 1.3,
              }}
            >
              {text}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

// ── Scene 3: Network Visualization ──────────────────────────────────
function NetworkScene() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const nodes = [
    { x: 640, y: 280, label: "Coach", color: COLORS.primary, r: 32 },
    { x: 420, y: 180, label: "Safety", color: COLORS.red500, r: 24 },
    { x: 860, y: 180, label: "Tools", color: COLORS.violet500, r: 24 },
    { x: 340, y: 360, label: "Patient", color: COLORS.blue500, r: 24 },
    { x: 940, y: 360, label: "Clinician", color: COLORS.amber500, r: 24 },
    { x: 520, y: 440, label: "Goals", color: COLORS.cyan500, r: 20 },
    { x: 760, y: 440, label: "Alerts", color: COLORS.red500, r: 20 },
  ];

  const edges = [
    [0, 1],
    [0, 2],
    [0, 3],
    [0, 4],
    [0, 5],
    [0, 6],
    [1, 3],
    [2, 4],
    [5, 3],
    [6, 4],
  ];

  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Center node pulse
  const pulse =
    1 + Math.sin(frame * 0.08) * 0.06;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.background,
        opacity: fadeIn,
      }}
    >
      <svg
        width="1280"
        height="720"
        viewBox="0 0 1280 720"
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        {/* Edges */}
        {edges.map(([from, to], i) => {
          const edgeDelay = 20 + i * 3;
          const edgeProgress = spring({
            frame,
            fps,
            config: { damping: 200, stiffness: 60 },
            delay: edgeDelay,
          });
          const n1 = nodes[from];
          const n2 = nodes[to];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;

          return (
            <line
              key={`edge-${i}`}
              x1={n1.x}
              y1={n1.y}
              x2={n1.x + dx * edgeProgress}
              y2={n1.y + dy * edgeProgress}
              stroke={COLORS.border}
              strokeWidth={1.5}
              opacity={0.5}
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node, i) => {
          const nodeEntrance = spring({
            frame,
            fps,
            config: { damping: 10, stiffness: 100 },
            delay: i * 5,
          });
          const scale = i === 0 ? nodeEntrance * pulse : nodeEntrance;

          return (
            <g
              key={`node-${i}`}
              transform={`translate(${node.x}, ${node.y}) scale(${scale})`}
            >
              <circle
                r={node.r}
                fill={node.color}
                opacity={0.9}
              />
              <circle
                r={node.r + 6}
                fill="none"
                stroke={node.color}
                strokeWidth={1}
                opacity={0.3}
              />
              <text
                y={node.r + 20}
                textAnchor="middle"
                fontFamily={FONTS.body}
                fontSize={12}
                fontWeight={500}
                fill={COLORS.mutedForeground}
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Bottom metrics */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 24,
        }}
      >
        {[
          { label: "701 Tests", delay: 50 },
          { label: "17 Graph Nodes", delay: 55 },
          { label: "5 AI Tools", delay: 60 },
        ].map((item, i) => {
          const entrance = spring({
            frame,
            fps,
            config: { damping: 20, stiffness: 60 },
            delay: item.delay,
          });
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 24 }}>
              {i > 0 && (
                <div
                  style={{
                    width: 1,
                    height: 16,
                    backgroundColor: COLORS.border,
                    opacity: entrance,
                  }}
                />
              )}
              <span
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 14,
                  color: COLORS.mutedForeground,
                  opacity: entrance,
                  transform: `translateY(${interpolate(entrance, [0, 1], [10, 0])}px)`,
                }}
              >
                {item.label}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

// ── Hero Preview Composition ────────────────────────────────────────
export const HeroPreview: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.background }}>
      <Sequence
        from={HERO_SCENES.title.from}
        durationInFrames={HERO_SCENES.title.duration}
      >
        <TitleScene />
      </Sequence>

      <Sequence
        from={HERO_SCENES.valueProps.from}
        durationInFrames={HERO_SCENES.valueProps.duration}
      >
        <ValuePropsScene />
      </Sequence>

      <Sequence
        from={HERO_SCENES.network.from}
        durationInFrames={HERO_SCENES.network.duration}
      >
        <NetworkScene />
      </Sequence>
    </AbsoluteFill>
  );
};
