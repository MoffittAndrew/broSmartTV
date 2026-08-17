import { clampInt, roundToEven } from './config.js';

export function applyGeometryUpdate(currentValue, nextValue, decreaseSamples, allowDecrease) {
  if (nextValue === null || !Number.isFinite(nextValue) || nextValue <= 0) {
    return { value: currentValue, didChange: false, decreaseSamples: 0 };
  }

  if (currentValue === null) {
    return { value: nextValue, didChange: true, decreaseSamples: 0 };
  }

  if (nextValue > currentValue) {
    return { value: nextValue, didChange: true, decreaseSamples: 0 };
  }

  if (nextValue === currentValue) {
    return { value: currentValue, didChange: false, decreaseSamples: 0 };
  }

  const shrinkAmount = currentValue - nextValue;
  const shrinkThreshold = Math.max(
    2,
    Math.round(currentValue * 0.03),
  );

  if (!allowDecrease || shrinkAmount < shrinkThreshold) {
    return { value: currentValue, didChange: false, decreaseSamples: 0 };
  }

  const nextDecreaseSamples = decreaseSamples + 1;
  if (nextDecreaseSamples >= 3) {
    return { value: nextValue, didChange: true, decreaseSamples: 0 };
  }

  return { value: currentValue, didChange: false, decreaseSamples: nextDecreaseSamples };
}

export function getAspectRatioFromSettings(settings) {
  if (!settings) {
    return null;
  }

  const explicitAspectRatio = Number(settings.aspectRatio);
  if (Number.isFinite(explicitAspectRatio) && explicitAspectRatio > 0) {
    return explicitAspectRatio;
  }

  const width = Number(settings.width);
  const height = Number(settings.height);
  if (Number.isFinite(width) && Number.isFinite(height) && width > 0 && height > 0) {
    return width / height;
  }

  return null;
}

export function getScreenHintGeometry(state) {
  if (!window.screen) {
    return { width: null, height: null };
  }

  const screenWidth = Number(window.screen.width);
  const screenHeight = Number(window.screen.height);
  if (!Number.isFinite(screenWidth) || !Number.isFinite(screenHeight) || screenWidth <= 0 || screenHeight <= 0) {
    return { width: null, height: null };
  }

  return {
    width: clampInt(screenWidth, state.captureSettings.width),
    height: clampInt(screenHeight, state.captureSettings.height),
  };
}

export function resolveAspectMatchedProfile(profile, state) {
  if (!profile || !Number.isFinite(state.captureSourceAspectRatio) || state.captureSourceAspectRatio <= 0) {
    return profile;
  }

  const maxWidth = clampInt(profile.width, state.captureSettings.width);
  const maxHeight = clampInt(profile.height, state.captureSettings.height);

  let width = maxWidth;
  let height = roundToEven(width / state.captureSourceAspectRatio, maxHeight);

  if (height > maxHeight) {
    height = maxHeight;
    width = roundToEven(height * state.captureSourceAspectRatio, maxWidth);
  }

  return {
    width: Math.max(2, Math.min(maxWidth, width)),
    height: Math.max(2, Math.min(maxHeight, height)),
    frameRate: profile.frameRate,
  };
}

export function getNormalizedCaptureGeometry(settings, state) {
  const width = Number(settings && settings.width);
  const height = Number(settings && settings.height);

  let normalizedWidth = Number.isFinite(width) && width > 0
    ? clampInt(width, state.captureSourceWidth || state.captureSettings.width)
    : null;
  let normalizedHeight = Number.isFinite(height) && height > 0
    ? clampInt(height, state.captureSourceHeight || state.captureSettings.height)
    : null;

  const displaySurface = settings && typeof settings.displaySurface === 'string'
    ? settings.displaySurface
    : null;
  const screenHint = getScreenHintGeometry(state);

  if ((displaySurface === 'monitor' || displaySurface === 'window') && normalizedWidth !== null && normalizedHeight !== null) {
    const screenWidth = screenHint.width;
    const screenHeight = screenHint.height;
    if (screenWidth !== null && screenHeight !== null) {
      const widthDelta = Math.abs(screenWidth - normalizedWidth);
      const heightDelta = Math.abs(screenHeight - normalizedHeight);
      const shouldSnapToScreen = widthDelta <= 16 && heightDelta <= 16;
      if (shouldSnapToScreen) {
        normalizedWidth = screenWidth;
        normalizedHeight = screenHeight;
      }
    }
  }

  if ((displaySurface === 'monitor' || displaySurface === 'window') && screenHint.width !== null && screenHint.height !== null) {
    const referenceWidth = normalizedWidth !== null ? normalizedWidth : state.captureSourceWidth || state.captureSettings.width;
    const referenceHeight = normalizedHeight !== null ? normalizedHeight : state.captureSourceHeight || state.captureSettings.height;
    const widthGrowth = screenHint.width - referenceWidth;
    const heightGrowth = screenHint.height - referenceHeight;
    if (widthGrowth >= 64 || heightGrowth >= 64) {
      normalizedWidth = Math.min(screenHint.width, state.captureSettings.width);
      normalizedHeight = Math.min(screenHint.height, state.captureSettings.height);
    }
  }

  return {
    width: normalizedWidth,
    height: normalizedHeight,
    displaySurface,
  };
}

export function updateCaptureSourceGeometry(settings, options = {}, state) {
  let didChange = false;
  const allowDecrease = options.allowDecrease === true;
  const normalized = getNormalizedCaptureGeometry(settings, state);

  if (normalized.displaySurface !== null && normalized.displaySurface !== state.captureDisplaySurface) {
    state.captureDisplaySurface = normalized.displaySurface;
  }

  const nextAspectRatio = getAspectRatioFromSettings(settings);
  if (
    Number.isFinite(nextAspectRatio)
    && nextAspectRatio > 0
    && nextAspectRatio !== state.captureSourceAspectRatio
    && (state.captureSourceAspectRatio === null || allowDecrease || nextAspectRatio > state.captureSourceAspectRatio)
  ) {
    state.captureSourceAspectRatio = nextAspectRatio;
    didChange = true;
  }

  if (normalized.width !== null) {
    const widthResult = applyGeometryUpdate(
      state.captureSourceWidth,
      normalized.width,
      state.captureSourceWidthDecreaseSamples,
      allowDecrease,
    );
    if (widthResult.didChange) {
      state.captureSourceWidth = widthResult.value;
      didChange = true;
    }
    state.captureSourceWidthDecreaseSamples = widthResult.decreaseSamples;
  }

  if (normalized.height !== null) {
    const heightResult = applyGeometryUpdate(
      state.captureSourceHeight,
      normalized.height,
      state.captureSourceHeightDecreaseSamples,
      allowDecrease,
    );
    if (heightResult.didChange) {
      state.captureSourceHeight = heightResult.value;
      didChange = true;
    }
    state.captureSourceHeightDecreaseSamples = heightResult.decreaseSamples;
  }

  return didChange;
}
