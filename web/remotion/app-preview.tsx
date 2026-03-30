import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import {
  COLORS,
  VIDEO_FPS,
  VIDEO_WIDTH,
  VIDEO_HEIGHT,
  FEATURE_DURATION,
  FEATURE_SCENES,
} from "./constants";
import { IntroScene } from "./scenes/intro-scene";
import { ArchitectureScene } from "./scenes/architecture-scene";
import { SafetyScene } from "./scenes/safety-scene";
import { PhasesScene } from "./scenes/phases-scene";
import { OutroScene } from "./scenes/outro-scene";

export {
  FEATURE_DURATION,
  VIDEO_FPS as APP_PREVIEW_FPS,
  VIDEO_WIDTH as APP_PREVIEW_WIDTH,
  VIDEO_HEIGHT as APP_PREVIEW_HEIGHT,
};

// ── Dot Grid Background ─────────────────────────────────────────────
function DotGrid() {
  const dots: { x: number; y: number }[] = [];
  const spacing = 40;
  for (let x = spacing; x < 1280; x += spacing) {
    for (let y = spacing; y < 720; y += spacing) {
      dots.push({ x, y });
    }
  }

  return (
    <svg
      width="1280"
      height="720"
      viewBox="0 0 1280 720"
      style={{ position: "absolute", top: 0, left: 0, opacity: 0.25 }}
    >
      {dots.map((dot, i) => (
        <circle key={i} cx={dot.x} cy={dot.y} r={1} fill={COLORS.border} />
      ))}
    </svg>
  );
}

// ── Progress Bar ────────────────────────────────────────────────────
function ProgressBar() {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        height: 3,
        backgroundColor: COLORS.muted,
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: "100%",
          backgroundColor: COLORS.primary,
        }}
      />
    </div>
  );
}

// ── App Preview Composition ─────────────────────────────────────────
export const AppPreview: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.background }}>
      <DotGrid />

      <Sequence
        from={FEATURE_SCENES.intro.from}
        durationInFrames={FEATURE_SCENES.intro.duration}
      >
        <IntroScene />
      </Sequence>

      <Sequence
        from={FEATURE_SCENES.architecture.from}
        durationInFrames={FEATURE_SCENES.architecture.duration}
      >
        <ArchitectureScene />
      </Sequence>

      <Sequence
        from={FEATURE_SCENES.safety.from}
        durationInFrames={FEATURE_SCENES.safety.duration}
      >
        <SafetyScene />
      </Sequence>

      <Sequence
        from={FEATURE_SCENES.phases.from}
        durationInFrames={FEATURE_SCENES.phases.duration}
      >
        <PhasesScene />
      </Sequence>

      <Sequence
        from={FEATURE_SCENES.outro.from}
        durationInFrames={FEATURE_SCENES.outro.duration}
      >
        <OutroScene />
      </Sequence>

      <ProgressBar />
    </AbsoluteFill>
  );
};
