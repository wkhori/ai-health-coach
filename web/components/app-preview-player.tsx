"use client";

import { Player } from "@remotion/player";
import {
  AppPreview,
  FEATURE_DURATION,
  APP_PREVIEW_FPS,
  APP_PREVIEW_WIDTH,
  APP_PREVIEW_HEIGHT,
} from "@/remotion/app-preview";

export function AppPreviewPlayer() {
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
        component={AppPreview}
        durationInFrames={FEATURE_DURATION}
        fps={APP_PREVIEW_FPS}
        compositionWidth={APP_PREVIEW_WIDTH}
        compositionHeight={APP_PREVIEW_HEIGHT}
        style={{ width: "100%" }}
        autoPlay
        loop
        acknowledgeRemotionLicense
      />
    </div>
  );
}
