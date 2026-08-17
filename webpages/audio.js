import { APP_CONSTANTS } from './config.js';
import { resolveAspectMatchedProfile } from './geometry.js';
import { bitrateBoundsForProfile, profileForMode } from './quality-policy.js';

export function buildAudioConstraints(audioEnabled) {
  if (!audioEnabled) {
    return false;
  }

  return {
    echoCancellation: false,
    noiseSuppression: false,
    autoGainControl: false,
    channelCount: 2,
    sampleRate: 48000,
    latency: 0,
    suppressLocalAudioPlayback: true,
  };
}

export function buildDisplayMediaOptions(profile, state, { strictVideoHints }) {
  const commonVideo = {
    width: { ideal: profile.width },
    height: { ideal: profile.height },
    aspectRatio: { ideal: state.captureSourceAspectRatio || (profile.width / profile.height) },
    frameRate: { ideal: profile.frameRate, max: profile.frameRate },
    logicalSurface: true,
  };

  const video = strictVideoHints
    ? {
        ...commonVideo,
        displaySurface: 'window',
        cursor: 'always',
      }
    : commonVideo;

  return {
    video,
    audio: buildAudioConstraints(state.audioEnabled),
    monitorTypeSurfaces: 'exclude',
    selfBrowserSurface: 'exclude',
    surfaceSwitching: 'include',
    windowAudio: 'window',
    systemAudio: 'exclude',
  };
}

export function isDisplayMediaConstraintCompatibilityError(err) {
  return err instanceof TypeError
    || (err && typeof err.name === 'string' && ['OverconstrainedError', 'NotFoundError'].includes(err.name));
}

export function getPreferredVideoCodecs() {
  if (typeof RTCRtpSender === 'undefined' || typeof RTCRtpSender.getCapabilities !== 'function') {
    return [];
  }

  const caps = RTCRtpSender.getCapabilities('video');
  if (!caps || !Array.isArray(caps.codecs)) {
    return [];
  }

  const nonMediaMimes = new Set(['video/rtx', 'video/red', 'video/ulpfec']);
  const mediaCodecs = caps.codecs.filter((codec) => !nonMediaMimes.has((codec.mimeType || '').toLowerCase()));
  if (mediaCodecs.length === 0) {
    return [];
  }

  const preferredOrder = ['video/VP9', 'video/VP8', 'video/H264'];
  const orderedMediaCodecs = [];
  for (const mimeType of preferredOrder) {
    for (const codec of mediaCodecs) {
      if (codec.mimeType === mimeType) {
        orderedMediaCodecs.push(codec);
      }
    }
  }

  for (const codec of mediaCodecs) {
    if (!orderedMediaCodecs.includes(codec)) {
      orderedMediaCodecs.push(codec);
    }
  }

  return orderedMediaCodecs;
}

export async function applyAudioSenderEncodingPolicy(sender, reason) {
  if (!sender || typeof sender.getParameters !== 'function' || typeof sender.setParameters !== 'function') {
    return;
  }

  const parameters = sender.getParameters();
  parameters.encodings = parameters.encodings && parameters.encodings.length > 0 ? parameters.encodings : [{}];
  const primaryEncoding = parameters.encodings[0];
  primaryEncoding.maxBitrate = APP_CONSTANTS.AUDIO_SENDER_MAX_BITRATE_BPS;
  primaryEncoding.minBitrate = APP_CONSTANTS.AUDIO_SENDER_MIN_BITRATE_BPS;
  delete primaryEncoding.scalabilityMode;
  delete parameters.degradationPreference;

  try {
    await sender.setParameters(parameters);
  } catch (err) {
    console.warn(`Unable to apply audio sender policy (${reason}):`, err);
  }
}

export async function applySenderEncodingPolicy(sender, profile, reason, state) {
  if (!sender || typeof sender.getParameters !== 'function' || typeof sender.setParameters !== 'function') {
    return;
  }

  const resolvedProfile = resolveAspectMatchedProfile(profile || profileForMode(state.currentQualityMode, state), state);
  const bitrateBounds = bitrateBoundsForProfile(resolvedProfile, state);
  const parameters = sender.getParameters();
  parameters.encodings = parameters.encodings && parameters.encodings.length > 0 ? parameters.encodings : [{}];

  const primaryEncoding = parameters.encodings[0];
  primaryEncoding.maxFramerate = resolvedProfile.frameRate;
  primaryEncoding.maxBitrate = bitrateBounds.maxBitrate;
  if (bitrateBounds.minBitrate > 0) {
    primaryEncoding.minBitrate = bitrateBounds.minBitrate;
  } else {
    delete primaryEncoding.minBitrate;
  }

  primaryEncoding.scalabilityMode = 'L1T1';
  parameters.degradationPreference = state.senderPolicy.degradationPreference;

  try {
    await sender.setParameters(parameters);
  } catch (err) {
    console.warn(`Full sender policy rejected (${reason}); retrying compatibility subset.`, err);
    delete primaryEncoding.minBitrate;
    delete primaryEncoding.scalabilityMode;
    delete parameters.degradationPreference;
    try {
      await sender.setParameters(parameters);
    } catch (fallbackErr) {
      console.warn(`Unable to apply sender encoding policy (${reason}):`, fallbackErr);
      return;
    }
  }
}
