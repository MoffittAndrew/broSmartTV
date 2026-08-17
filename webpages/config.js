export const APP_CONSTANTS = {
  SOURCE_GEOMETRY_DECREASE_STABLE_SAMPLES: 3,
  SOURCE_GEOMETRY_DECREASE_MIN_FRACTION: 0.03,
  ICE_GATHER_TIMEOUT_MS: 8000,
  CONNECTION_TIMEOUT_MS: 10000,
  LOW_MOTION_FPS_THRESHOLD: 2,
  LOW_MOTION_BITRATE_BPS_THRESHOLD: 120000,
  AUDIO_SENDER_MAX_BITRATE_BPS: 256_000,
  AUDIO_SENDER_MIN_BITRATE_BPS: 128_000,
};

export const DEFAULT_CAPTURE_SETTINGS = {
  width: 1920,
  height: 1080,
  frameRate: 30,
};

export const DEFAULT_ADAPTIVE_POLICY = {
  lowFpsThreshold: 30,
  lowSampleWindow: 10,
  lowSampleRequired: 10,
  recoveryFpsThreshold: 35,
  recoverySampleWindow: 20,
  recoverySampleRequired: 18,
  downgradeCooldownSeconds: 20,
  upgradeCooldownSeconds: 60,
  minWidth: 1280,
  minHeight: 720,
  maxWidth: 1920,
  maxHeight: 1080,
};

export const DEFAULT_SENDER_POLICY = {
  degradationPreference: "maintain-framerate",
  bitrateMaxBps1080p: 5_000_000,
  bitrateMinBps1080p: 0,
  bitrateMaxBps720p: 2_800_000,
  bitrateMinBps720p: 0,
};

export function clampInt(value, fallback) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.round(parsed);
}

export function roundToEven(value, fallback) {
  const rounded = clampInt(value, fallback);
  if (rounded <= 0) {
    return fallback;
  }
  return rounded % 2 === 0 ? rounded : rounded - 1;
}
