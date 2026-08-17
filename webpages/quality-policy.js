import { clampInt, roundToEven } from './config.js';
import { resolveAspectMatchedProfile } from './geometry.js';

export function profilesMatch(leftProfile, rightProfile) {
  return !!leftProfile
    && !!rightProfile
    && leftProfile.width === rightProfile.width
    && leftProfile.height === rightProfile.height
    && leftProfile.frameRate === rightProfile.frameRate;
}

export function getHighProfileBase(state) {
  return {
    width: state.captureSourceWidth && state.captureSourceWidth > 0
      ? Math.min(state.adaptivePolicy.maxWidth, state.captureSourceWidth)
      : state.adaptivePolicy.maxWidth,
    height: state.captureSourceHeight && state.captureSourceHeight > 0
      ? Math.min(state.adaptivePolicy.maxHeight, state.captureSourceHeight)
      : state.adaptivePolicy.maxHeight,
    frameRate: state.captureSettings.frameRate,
  };
}

export function getLowProfileBase(state) {
  const highProfile = getHighProfileBase(state);
  const scaledWidth = Math.max(2, roundToEven(highProfile.width * 0.75, highProfile.width));
  const scaledHeight = Math.max(2, roundToEven(highProfile.height * 0.75, highProfile.height));

  if (
    state.captureSourceWidth && state.captureSourceHeight
    && (state.captureSourceWidth < state.adaptivePolicy.minWidth && state.captureSourceHeight < state.adaptivePolicy.minHeight)
  ) {
    return {
      width: Math.max(2, roundToEven(highProfile.width / 2, highProfile.width)),
      height: Math.max(2, roundToEven(highProfile.height / 2, highProfile.height)),
      frameRate: state.captureSettings.frameRate,
    };
  }

  return {
    width: Math.max(state.adaptivePolicy.minWidth, scaledWidth),
    height: Math.max(state.adaptivePolicy.minHeight, scaledHeight),
    frameRate: state.captureSettings.frameRate,
  };
}

export function profileForMode(mode, state) {
  if (mode === 'floor') {
    return resolveAspectMatchedProfile(getLowProfileBase(state), state);
  }

  return resolveAspectMatchedProfile(getHighProfileBase(state), state);
}

export function modeFromProfile(profile, state) {
  if (!profile) {
    return 'high';
  }
  if (profile.width <= state.adaptivePolicy.minWidth && profile.height <= state.adaptivePolicy.minHeight) {
    return 'floor';
  }
  return 'high';
}

export function bitrateBoundsForProfile(profile, state) {
  const resolvedProfile = resolveAspectMatchedProfile(profile || profileForMode(state.currentQualityMode, state), state);
  const width = clampInt(resolvedProfile && resolvedProfile.width, state.adaptivePolicy.maxWidth);
  const height = clampInt(resolvedProfile && resolvedProfile.height, state.adaptivePolicy.maxHeight);
  const pixelCount = width * height;

  if (pixelCount <= state.adaptivePolicy.minWidth * state.adaptivePolicy.minHeight) {
    return {
      minBitrate: state.senderPolicy.bitrateMinBps720p,
      maxBitrate: state.senderPolicy.bitrateMaxBps720p,
    };
  }

  return {
    minBitrate: state.senderPolicy.bitrateMinBps1080p,
    maxBitrate: state.senderPolicy.bitrateMaxBps1080p,
  };
}

export function maxSampleWindowSize(state) {
  return Math.max(state.adaptivePolicy.lowSampleWindow, state.adaptivePolicy.recoverySampleWindow);
}

export function pushFpsSample(fpsValue, state) {
  if (!Number.isFinite(fpsValue)) {
    return;
  }
  state.fpsSamples.push(Math.round(fpsValue));
  const maxSize = maxSampleWindowSize(state);
  if (state.fpsSamples.length > maxSize) {
    state.fpsSamples = state.fpsSamples.slice(state.fpsSamples.length - maxSize);
  }
}

export function countWindowByPredicate(windowSize, predicate, state) {
  if (state.fpsSamples.length < windowSize) {
    return null;
  }
  const recent = state.fpsSamples.slice(state.fpsSamples.length - windowSize);
  return recent.filter(predicate).length;
}
