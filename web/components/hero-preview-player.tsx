"use client";

import { Player } from "@remotion/player";
import {
  HeroPreview,
  HERO_DURATION,
  HERO_FPS,
  HERO_WIDTH,
  HERO_HEIGHT,
} from "@/remotion/hero-preview";

export function HeroPreviewPlayer() {
  return (
    <div
      style={{
        borderRadius: 16,
        overflow: "hidden",
        border: "1px solid var(--color-border)",
        boxShadow: "0 8px 40px rgba(0, 0, 0, 0.12)",
      }}
    >
      <Player
        component={HeroPreview}
        durationInFrames={HERO_DURATION}
        fps={HERO_FPS}
        compositionWidth={HERO_WIDTH}
        compositionHeight={HERO_HEIGHT}
        style={{ width: "100%" }}
        autoPlay
        loop
        acknowledgeRemotionLicense
      />
    </div>
  );
}
