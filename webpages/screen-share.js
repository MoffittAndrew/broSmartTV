import {
  APP_CONSTANTS,
  DEFAULT_CAPTURE_SETTINGS,
  DEFAULT_ADAPTIVE_POLICY,
  DEFAULT_SENDER_POLICY,
  clampInt,
} from './config.js';

import {
  resolveAspectMatchedProfile,
  updateCaptureSourceGeometry,
} from './geometry.js';

import {
  countWindowByPredicate,
  modeFromProfile,
  profileForMode,
  profilesMatch,
  pushFpsSample,
} from './quality-policy.js';

import {
  applyAudioSenderEncodingPolicy,
  applySenderEncodingPolicy,
  buildDisplayMediaOptions,
  getPreferredVideoCodecs,
  isDisplayMediaConstraintCompatibilityError,
} from './audio.js';

export const state = {
  pc: null,
  stream: null,
  videoSender: null,
  fpsMonitor: null,
  connectionTimeoutId: null,
  isStreaming: false,
  isStarting: false,
  isAdaptiveRestartInProgress: false,
  isLowMotionContent: false,
  currentFps: 'unknown',
  currentWidth: 'unknown',
  currentHeight: 'unknown',
  captureSettings: { ...DEFAULT_CAPTURE_SETTINGS },
  iceServers: [],
  captureSourceAspectRatio: null,
  captureSourceWidth: null,
  captureSourceHeight: null,
  captureDisplaySurface: null,
  audioEnabled: true,
  isAudioActive: false,
  audioWarning: null,
  adaptivePolicy: { ...DEFAULT_ADAPTIVE_POLICY },
  senderPolicy: { ...DEFAULT_SENDER_POLICY },
  currentQualityMode: 'high',
  qualityControlMode: 'auto',
  activeProfile: null,
  fpsSamples: [],
  lastQualityChangeAtMs: 0,
  captureSourceWidthDecreaseSamples: 0,
  captureSourceHeightDecreaseSamples: 0,
};

function countSdpCandidates(sdp) {
  if (!sdp) {
    return 0;
  }
  return sdp.split('\n').filter((line) => line.startsWith('a=candidate:')).length;
}

function clearConnectionTimeout() {
  if (state.connectionTimeoutId !== null) {
    clearTimeout(state.connectionTimeoutId);
    state.connectionTimeoutId = null;
  }
}

function startConnectionTimeout() {
  clearConnectionTimeout();
  state.connectionTimeoutId = setTimeout(() => {
    console.warn(`Connection timed out after ${APP_CONSTANTS.CONNECTION_TIMEOUT_MS / 1000}s without reaching connected state.`);
    stopStream('connection timed out');
  }, APP_CONSTANTS.CONNECTION_TIMEOUT_MS);
}

function updateStreamingStatus(statusDiv) {
  const audioStatus = state.isAudioActive ? 'audio:on' : 'audio:off';
  const warningSuffix = state.audioWarning ? ` (${state.audioWarning})` : '';
  statusDiv.textContent = `✅ streaming active (${state.currentWidth}x${state.currentHeight} @ ${state.currentFps}fps, ${audioStatus})${warningSuffix}`;
}

async function evaluateAdaptiveQuality() {
  if (state.qualityControlMode !== 'auto') {
    return;
  }

  if (!state.isStreaming || state.isStarting || state.isAdaptiveRestartInProgress) {
    return;
  }

  const nowMs = Date.now();

  if (state.currentQualityMode === 'high') {
    const lowCount = countWindowByPredicate(
      state.adaptivePolicy.lowSampleWindow,
      (sample) => sample < state.adaptivePolicy.lowFpsThreshold,
      state,
    );

    if (lowCount !== null && lowCount >= state.adaptivePolicy.lowSampleRequired) {
      const elapsedSinceLastChangeMs = nowMs - state.lastQualityChangeAtMs;
      const cooldownMs = state.adaptivePolicy.downgradeCooldownSeconds * 1000;
      if (state.lastQualityChangeAtMs !== 0 && elapsedSinceLastChangeMs < cooldownMs) {
        return;
      }

      const target = profileForMode('floor', state);
      await requestAdaptiveQualitySwitch(target, 'floor', `fps below ${state.adaptivePolicy.lowFpsThreshold} for ${state.adaptivePolicy.lowSampleRequired}/${state.adaptivePolicy.lowSampleWindow} samples`);
    }

    return;
  }

  if (state.currentQualityMode === 'floor') {
    const recoveryCount = countWindowByPredicate(
      state.adaptivePolicy.recoverySampleWindow,
      (sample) => sample >= state.adaptivePolicy.recoveryFpsThreshold,
      state,
    );

    if (recoveryCount !== null && recoveryCount >= state.adaptivePolicy.recoverySampleRequired) {
      const elapsedSinceLastChangeMs = nowMs - state.lastQualityChangeAtMs;
      const cooldownMs = state.adaptivePolicy.upgradeCooldownSeconds * 1000;
      if (state.lastQualityChangeAtMs !== 0 && elapsedSinceLastChangeMs < cooldownMs) {
        return;
      }

      const target = profileForMode('high', state);
      await requestAdaptiveQualitySwitch(target, 'high', `fps recovered above ${state.adaptivePolicy.recoveryFpsThreshold} for ${state.adaptivePolicy.recoverySampleRequired}/${state.adaptivePolicy.recoverySampleWindow} samples`);
    }
  }
}

async function applyQualityControlMode(mode, qualitySelect) {
  state.qualityControlMode = mode;
  qualitySelect.value = mode;

  if (!state.isStreaming) {
    return;
  }

  if (mode === 'auto') {
    state.fpsSamples = [];
    return;
  }

  const targetMode = mode === 'high' ? 'high' : 'floor';
  if (targetMode === state.currentQualityMode) {
    return;
  }

  await requestAdaptiveQualitySwitch(profileForMode(targetMode, state), targetMode, `manual mode ${mode}`);
}

function stopFpsMonitor(resetStatus = true) {
  if (state.fpsMonitor) {
    clearInterval(state.fpsMonitor);
    state.fpsMonitor = null;
  }
  if (resetStatus) {
    state.currentFps = 'unknown';
    state.currentWidth = 'unknown';
    state.currentHeight = 'unknown';
  }
  state.fpsSamples = [];
  state.isLowMotionContent = false;
  state.videoSender = null;
}

function startFpsMonitor(sender, statusDiv) {
  stopFpsMonitor(false);
  if (!sender || typeof sender.getStats !== 'function') {
    return;
  }

  let lastTimestamp = null;
  let lastFramesEncoded = null;
  let lastBytesSent = null;
  let lastSenderLogAt = 0;

  state.fpsMonitor = setInterval(async () => {
    try {
      const stats = await sender.getStats();
      let videoStat = null;
      stats.forEach((report) => {
        if (!videoStat && report.type === 'outbound-rtp' && report.kind === 'video') {
          videoStat = report;
        }
      });

      if (!videoStat) {
        state.currentFps = 'unknown';
        updateStreamingStatus(statusDiv);
        return;
      }

      const timestamp = videoStat.timestamp;
      const framesEncoded = typeof videoStat.framesEncoded === 'number'
        ? videoStat.framesEncoded
        : (typeof videoStat.framesSent === 'number' ? videoStat.framesSent : null);
      const bytesSent = typeof videoStat.bytesSent === 'number' ? videoStat.bytesSent : null;
      let currentBitrateBps = null;
      let sampledFps = null;

      if (lastTimestamp !== null && lastFramesEncoded !== null && framesEncoded !== null) {
        const elapsedSeconds = (timestamp - lastTimestamp) / 1000;
        if (elapsedSeconds > 0) {
          const fps = (framesEncoded - lastFramesEncoded) / elapsedSeconds;
          if (Number.isFinite(fps)) {
            const rounded = Math.round(fps);
            sampledFps = rounded;
            state.currentFps = String(rounded);
          } else {
            state.currentFps = 'unknown';
          }

          if (bytesSent !== null && lastBytesSent !== null) {
            const deltaBytes = bytesSent - lastBytesSent;
            currentBitrateBps = Math.max(0, (deltaBytes * 8) / elapsedSeconds);
          }
        }
      }

      if (framesEncoded !== null) {
        lastTimestamp = timestamp;
        lastFramesEncoded = framesEncoded;
      }
      if (bytesSent !== null) {
        lastBytesSent = bytesSent;
      }

      const lowMotionDetected = sampledFps !== null
        && sampledFps <= APP_CONSTANTS.LOW_MOTION_FPS_THRESHOLD
        && Number.isFinite(currentBitrateBps)
        && currentBitrateBps <= APP_CONSTANTS.LOW_MOTION_BITRATE_BPS_THRESHOLD;

      if (lowMotionDetected) {
        if (!state.isLowMotionContent) {
          console.log('Low-motion scene detected; pausing FPS-driven auto-downgrade.', { sampledFps, currentBitrateBps });
        }
        state.isLowMotionContent = true;
        state.fpsSamples = [];
        state.currentFps = '<idle>';

        if (state.qualityControlMode === 'auto' && state.currentQualityMode === 'floor' && !state.isAdaptiveRestartInProgress) {
          await requestAdaptiveQualitySwitch(profileForMode('high', state), 'high', 'low-motion scene prioritize detail');
        }
      } else {
        state.isLowMotionContent = false;
        if (sampledFps !== null) {
          pushFpsSample(sampledFps, state);
        }
      }

      const videoTrack = state.stream ? state.stream.getVideoTracks()[0] : null;
      const trackSettings = videoTrack && typeof videoTrack.getSettings === 'function'
        ? videoTrack.getSettings()
        : {};
      const allowSourceDecrease = state.currentQualityMode === 'high'
        && !!state.activeProfile
        && ((Number.isFinite(trackSettings.width) && trackSettings.width < state.activeProfile.width)
          || (Number.isFinite(trackSettings.height) && trackSettings.height < state.activeProfile.height));
      const geometryDidChange = updateCaptureSourceGeometry(trackSettings, { allowDecrease: allowSourceDecrease }, state);

      state.currentWidth = videoStat.frameWidth || trackSettings.width || state.currentWidth;
      state.currentHeight = videoStat.frameHeight || trackSettings.height || state.currentHeight;

      if (geometryDidChange) {
        await syncProfileToSourceGeometry('capture source resized');
      }

      if (timestamp - lastSenderLogAt >= 5000) {
        lastSenderLogAt = timestamp;
        const qualityLimitationReason = videoStat.qualityLimitationReason || 'unknown';
        const qualityLimitationDurations = videoStat.qualityLimitationDurations || {};
        const captureFps = typeof videoStat.framesPerSecond === 'number' ? Math.round(videoStat.framesPerSecond) : null;
        const frameWidth = videoStat.frameWidth || state.currentWidth;
        const frameHeight = videoStat.frameHeight || state.currentHeight;
        const codec = videoStat.codecId ? stats.get(videoStat.codecId) : null;
        const negotiatedCodec = codec && codec.mimeType ? codec.mimeType : 'unknown';
        console.log('Sender stats:', {
          fps: state.currentFps,
          frameWidth,
          frameHeight,
          captureFps,
          sourceWidth: state.captureSourceWidth,
          sourceHeight: state.captureSourceHeight,
          displaySurface: state.captureDisplaySurface,
          qualityLimitationReason,
          qualityLimitationDurations,
          bytesSent,
          currentBitrateBps,
          isLowMotionContent: state.isLowMotionContent,
          negotiatedCodec,
        });
      }

      updateStreamingStatus(statusDiv);
      if (!state.isLowMotionContent) {
        await evaluateAdaptiveQuality();
      }
    } catch (err) {
      console.warn('Failed to read outbound video stats:', err);
      state.currentFps = 'unknown';
      updateStreamingStatus(statusDiv);
    }
  }, 1000);
}

async function requestDisplayMedia(profile, statusDiv) {
  const strictConstraints = buildDisplayMediaOptions(profile, state, { strictVideoHints: true });
  const fallbackConstraints = buildDisplayMediaOptions(profile, state, { strictVideoHints: false });
  const videoOnlyFallbackConstraints = {
    ...fallbackConstraints,
    audio: false,
  };

  const validateSelectedSurface = (selectedStream) => {
    if (!selectedStream) {
      return selectedStream;
    }

    const selectedVideoTrack = selectedStream.getVideoTracks()[0];
    const selectedSettings = selectedVideoTrack && typeof selectedVideoTrack.getSettings === 'function'
      ? selectedVideoTrack.getSettings()
      : {};
    const selectedDisplaySurface = selectedSettings && typeof selectedSettings.displaySurface === 'string'
      ? selectedSettings.displaySurface
      : null;

    if (selectedDisplaySurface === 'monitor') {
      selectedStream.getTracks().forEach((track) => track.stop());
      throw new Error('please select a window or browser tab to share, full screen sharing is disabled for this app bruh');
    }

    return selectedStream;
  };

  if (navigator.mediaDevices && typeof navigator.mediaDevices.getDisplayMedia === 'function') {
    try {
      const selectedStream = await navigator.mediaDevices.getDisplayMedia(strictConstraints);
      return validateSelectedSurface(selectedStream);
    } catch (err) {
      if (isDisplayMediaConstraintCompatibilityError(err)) {
        try {
          const selectedStream = await navigator.mediaDevices.getDisplayMedia(fallbackConstraints);
          return validateSelectedSurface(selectedStream);
        } catch (fallbackErr) {
          if (state.audioEnabled && isDisplayMediaConstraintCompatibilityError(fallbackErr)) {
            console.warn('Audio capture constraints unsupported; continuing with video-only.', fallbackErr);
            const selectedStream = await navigator.mediaDevices.getDisplayMedia(videoOnlyFallbackConstraints);
            return validateSelectedSurface(selectedStream);
          }
          throw fallbackErr;
        }
      }
      throw err;
    }
  }

  if (typeof navigator.getDisplayMedia === 'function') {
    const selectedStream = await navigator.getDisplayMedia(fallbackConstraints);
    return validateSelectedSurface(selectedStream);
  }

  const origin = window.location.origin;
  const contextHint = window.isSecureContext ? '' : ` Screen capture requires HTTPS or localhost. Current origin: ${origin}`;
  throw new Error(`screen capture API is unavailable in this browser.${contextHint}`);
}

async function checkAvailability() {
  try {
    const res = await fetch('/status');
    if (res.ok) {
      const data = await res.json();
      return data.available;
    }
  } catch (err) {
    console.error('Status check failed:', err);
  }
  return false;
}

async function stopStream(reason = 'stopped', startBtn, statusDiv) {
  clearConnectionTimeout();
  state.isAdaptiveRestartInProgress = false;
  stopFpsMonitor();
  state.isStreaming = false;
  state.isStarting = false;
  state.isAudioActive = false;
  state.audioWarning = null;
  state.captureSourceAspectRatio = null;
  state.captureSourceWidth = null;
  state.captureSourceHeight = null;
  state.captureDisplaySurface = null;

  if (state.stream) {
    state.stream.getTracks().forEach((track) => track.stop());
    state.stream = null;
  }

  if (state.pc) {
    state.pc.close();
    state.pc = null;
  }

  startBtn.textContent = 'start screen share';
  startBtn.disabled = false;
  statusDiv.textContent = `🛑 stream ${reason}`;
  console.log('Stream stopped:', reason);
}

async function requestAdaptiveQualitySwitch(targetProfile, targetMode, reason, startBtn, statusDiv) {
  if (!state.isStreaming || state.isStarting || state.isAdaptiveRestartInProgress || !state.stream) {
    return;
  }

  state.isAdaptiveRestartInProgress = true;
  state.lastQualityChangeAtMs = Date.now();
  console.warn(`Adaptive quality switch -> ${targetMode}: ${reason}`);

  try {
    const videoTrack = state.stream.getVideoTracks()[0];
    if (!videoTrack) {
      return;
    }

    const resolvedProfile = resolveAspectMatchedProfile(targetProfile, state);

    await videoTrack.applyConstraints({
      width: { ideal: resolvedProfile.width },
      height: { ideal: resolvedProfile.height },
      aspectRatio: { ideal: state.captureSourceAspectRatio },
      frameRate: { ideal: resolvedProfile.frameRate, max: resolvedProfile.frameRate },
    });

    await applySenderEncodingPolicy(state.videoSender, resolvedProfile, `adaptive switch to ${targetMode}`, state);

    const settings = typeof videoTrack.getSettings === 'function' ? videoTrack.getSettings() : {};
    updateCaptureSourceGeometry(settings, { allowDecrease: false }, state);
    state.currentWidth = settings.width ?? resolvedProfile.width;
    state.currentHeight = settings.height ?? resolvedProfile.height;
    if (Number.isFinite(settings.frameRate)) {
      state.currentFps = String(Math.round(settings.frameRate));
    }

    state.fpsSamples = [];
    state.currentQualityMode = targetMode;
    state.activeProfile = resolvedProfile;
    updateStreamingStatus(statusDiv);
  } catch (err) {
    console.warn(`Adaptive quality switch failed (${targetMode}):`, err);
  } finally {
    state.isAdaptiveRestartInProgress = false;
  }
}

async function syncProfileToSourceGeometry(reason, statusDiv) {
  if (!state.isStreaming || state.isStarting || state.isAdaptiveRestartInProgress) {
    return;
  }

  const targetProfile = profileForMode(state.currentQualityMode, state);
  if (profilesMatch(state.activeProfile, targetProfile)) {
    return;
  }

  await requestAdaptiveQualitySwitch(targetProfile, state.currentQualityMode, reason, statusDiv);
}

async function loadCaptureSettings() {
  try {
    const response = await fetch('/capture-settings');
    if (!response.ok) {
      return;
    }

    const settings = await response.json();
    state.captureSettings = {
      width: clampInt(settings.width, state.captureSettings.width),
      height: clampInt(settings.height, state.captureSettings.height),
      frameRate: clampInt(settings.frameRate, state.captureSettings.frameRate),
    };

    state.iceServers = Array.isArray(settings.iceServers) ? settings.iceServers : [];

    state.adaptivePolicy = {
      lowFpsThreshold: clampInt(settings.adaptLowFpsThreshold, state.adaptivePolicy.lowFpsThreshold),
      lowSampleWindow: clampInt(settings.adaptLowSampleWindow, state.adaptivePolicy.lowSampleWindow),
      lowSampleRequired: clampInt(settings.adaptLowSampleRequired, state.adaptivePolicy.lowSampleRequired),
      recoveryFpsThreshold: clampInt(settings.adaptRecoveryFpsThreshold, state.adaptivePolicy.recoveryFpsThreshold),
      recoverySampleWindow: clampInt(settings.adaptRecoverySampleWindow, state.adaptivePolicy.recoverySampleWindow),
      recoverySampleRequired: clampInt(settings.adaptRecoverySampleRequired, state.adaptivePolicy.recoverySampleRequired),
      downgradeCooldownSeconds: clampInt(settings.adaptDowngradeCooldownSeconds, state.adaptivePolicy.downgradeCooldownSeconds),
      upgradeCooldownSeconds: clampInt(settings.adaptUpgradeCooldownSeconds, state.adaptivePolicy.upgradeCooldownSeconds),
      minWidth: clampInt(settings.adaptMinWidth, state.adaptivePolicy.minWidth),
      minHeight: clampInt(settings.adaptMinHeight, state.adaptivePolicy.minHeight),
      maxWidth: clampInt(settings.adaptMaxWidth, state.adaptivePolicy.maxWidth),
      maxHeight: clampInt(settings.adaptMaxHeight, state.adaptivePolicy.maxHeight),
    };

    state.senderPolicy = {
      degradationPreference: typeof settings.degradationPreference === 'string'
        ? settings.degradationPreference
        : state.senderPolicy.degradationPreference,
      bitrateMaxBps1080p: clampInt(settings.bitrateMaxBps1080p, state.senderPolicy.bitrateMaxBps1080p),
      bitrateMinBps1080p: clampInt(settings.bitrateMinBps1080p, state.senderPolicy.bitrateMinBps1080p),
      bitrateMaxBps720p: clampInt(settings.bitrateMaxBps720p, state.senderPolicy.bitrateMaxBps720p),
      bitrateMinBps720p: clampInt(settings.bitrateMinBps720p, state.senderPolicy.bitrateMinBps720p),
    };

    state.audioEnabled = settings.audioEnabled !== false;
  } catch (err) {
    console.error('Failed to load capture settings:', err);
  }
}

async function waitForIceGatheringComplete(peerConnection, timeoutMs = APP_CONSTANTS.ICE_GATHER_TIMEOUT_MS) {
  if (!peerConnection || peerConnection.iceGatheringState === 'complete') {
    return;
  }

  await new Promise((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeoutId);
      peerConnection.removeEventListener('icegatheringstatechange', handleStateChange);
      resolve();
    };

    const handleStateChange = () => {
      console.log('ICE gathering state:', peerConnection.iceGatheringState);
      if (peerConnection.iceGatheringState === 'complete') {
        finish();
      }
    };

    const timeoutId = setTimeout(() => {
      console.warn(`Timed out waiting ${timeoutMs}ms for ICE gathering; continuing with current offer.`);
      finish();
    }, timeoutMs);

    peerConnection.addEventListener('icegatheringstatechange', handleStateChange);
  });
}

async function startStreaming(options = {}, ui) {
  const { startBtn, qualitySelect, statusDiv } = ui;
  let selectedProfile = options.profile || null;
  const isAdaptiveRestart = options.isAdaptiveRestart === true;

  if (state.isStarting || state.isStreaming) {
    return;
  }

  state.isStarting = true;
  startBtn.disabled = true;

  if (!isAdaptiveRestart) {
    await loadCaptureSettings();
    state.activeProfile = profileForMode('high', state);
  }

  if (!selectedProfile) {
    selectedProfile = profileForMode(state.currentQualityMode, state);
  }

  const profile = selectedProfile || state.activeProfile || profileForMode('high', state);
  state.activeProfile = profile;

  const available = await checkAvailability();
  if (!available) {
    state.isStarting = false;
    startBtn.disabled = false;
    alert('Stream is currently busy. Try again later.');
    statusDiv.textContent = '❌ stream is busy rn bro';
    state.isAdaptiveRestartInProgress = false;
    return;
  }

  try {
    state.stream = await requestDisplayMedia(profile, statusDiv);
  } catch (err) {
    state.isStarting = false;
    startBtn.disabled = false;
    state.isAdaptiveRestartInProgress = false;
    console.error('User cancelled or error:', err);
    if (!window.isSecureContext) {
      statusDiv.textContent = '❌ screen share blocked: gotta open this page via HTTPS';
    } else {
      const reason = err && typeof err.message === 'string' && err.message.trim().length > 0 ? err.message.trim() : 'unable to start screen share';
      statusDiv.textContent = `❌ ${reason}`;
    }
    return;
  }

  const audioTracks = state.stream.getAudioTracks();
  const selectedVideoTrack = state.stream.getVideoTracks()[0];
  const selectedTrackSettings = selectedVideoTrack && typeof selectedVideoTrack.getSettings === 'function'
    ? selectedVideoTrack.getSettings()
    : {};
  const selectedDisplaySurface = selectedTrackSettings && typeof selectedTrackSettings.displaySurface === 'string'
    ? selectedTrackSettings.displaySurface
    : null;

  state.isAudioActive = audioTracks.length > 0;
  if (state.audioEnabled && !state.isAudioActive) {
    state.audioWarning = selectedDisplaySurface === 'window'
      ? 'window audio unavailable here; use tab capture for reliable app-only audio'
      : 'audio unavailable; streaming video only';
  } else if (selectedDisplaySurface === 'window') {
    state.audioWarning = 'window audio isolation depends on browser; tab capture is most reliable';
  } else {
    state.audioWarning = null;
  }

  const videoTrack = state.stream.getVideoTracks()[0];
  const initialSettings = videoTrack && typeof videoTrack.getSettings === 'function' ? videoTrack.getSettings() : {};
  updateCaptureSourceGeometry(initialSettings, { allowDecrease: true }, state);
  const resolvedProfile = profileForMode(state.currentQualityMode, state);
  try {
    await videoTrack.applyConstraints({
      width: { ideal: resolvedProfile.width },
      height: { ideal: resolvedProfile.height },
      aspectRatio: { ideal: state.captureSourceAspectRatio },
      frameRate: { ideal: resolvedProfile.frameRate, max: resolvedProfile.frameRate },
    });
  } catch (err) {
    console.warn('Unable to tighten video track constraints:', err);
  }

  state.pc = new RTCPeerConnection({
    iceServers: state.iceServers,
    iceCandidatePoolSize: 4,
  });
  const currentPc = state.pc;

  currentPc.onconnectionstatechange = () => {
    console.log('Connection state:', currentPc.connectionState);
    if (currentPc.connectionState === 'connected') {
      clearConnectionTimeout();
    }
    if (['disconnected', 'failed', 'closed'].includes(currentPc.connectionState)) {
      stopStream('disconnected', startBtn, statusDiv);
    }
  };

  currentPc.oniceconnectionstatechange = () => {
    console.log('ICE connection state:', currentPc.iceConnectionState);
  };

  currentPc.onicecandidate = (event) => {
    if (event.candidate) {
      console.log('ICE candidate gathered:', event.candidate.candidate);
    } else {
      console.log('ICE candidate gathering complete (null candidate event).');
    }
  };

  for (const track of state.stream.getTracks()) {
    const sender = currentPc.addTrack(track, state.stream);
    if (track.kind === 'video') {
      state.videoSender = sender;
      const videoTransceiver = currentPc.getTransceivers().find((transceiver) => transceiver.sender === sender);
      const preferredCodecs = getPreferredVideoCodecs();
      if (videoTransceiver && preferredCodecs.length > 0 && typeof videoTransceiver.setCodecPreferences === 'function') {
        videoTransceiver.setCodecPreferences(preferredCodecs);
      }
      await applySenderEncodingPolicy(sender, resolvedProfile, 'initial stream start', state);
    }
    if (track.kind === 'audio') {
      await applyAudioSenderEncodingPolicy(sender, 'initial stream start');
    }
  }

  const offer = await currentPc.createOffer();
  await currentPc.setLocalDescription(offer);
  await waitForIceGatheringComplete(currentPc);

  console.log('Offer candidate count:', countSdpCandidates(currentPc.localDescription && currentPc.localDescription.sdp));
  startConnectionTimeout();

  try {
    const response = await fetch('/offer', {
      method: 'POST',
      body: JSON.stringify(currentPc.localDescription),
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const message = await response.text();
      alert(message);
      await stopStream('rejected', startBtn, statusDiv);
      state.isAdaptiveRestartInProgress = false;
      return;
    }

    const answer = await response.json();
    await currentPc.setRemoteDescription(answer);
    console.log('Answer candidate count:', countSdpCandidates(answer.sdp));
  } catch (err) {
    console.error('Offer/answer exchange failed:', err);
    await stopStream('connection failed', startBtn, statusDiv);
    state.isAdaptiveRestartInProgress = false;
    return;
  }

  state.isStreaming = true;
  state.isStarting = false;
  state.isAdaptiveRestartInProgress = false;
  startBtn.disabled = false;
  startBtn.textContent = 'stop screen share';
  state.currentFps = 'starting';

  videoTrack.onended = () => {
    stopStream('ended by user', startBtn, statusDiv);
  };

  const settings = videoTrack && typeof videoTrack.getSettings === 'function' ? videoTrack.getSettings() : {};
  updateCaptureSourceGeometry(settings, { allowDecrease: false }, state);
  state.currentWidth = settings.width ?? resolvedProfile.width ?? 'unknown';
  state.currentHeight = settings.height ?? resolvedProfile.height ?? 'unknown';
  state.currentFps = Number.isFinite(settings.frameRate) ? String(Math.round(settings.frameRate)) : state.currentFps;

  state.currentQualityMode = modeFromProfile(resolvedProfile, state);
  state.activeProfile = resolvedProfile;
  console.log(`Capture settings: ${state.currentWidth}x${state.currentHeight} @ ${state.currentFps}fps`);
  updateStreamingStatus(statusDiv);

  startFpsMonitor(state.videoSender, statusDiv);
}

export function initScreenShareApp(ui = {}) {
  const startBtn = ui.startBtn ?? document.getElementById('startBtn');
  const qualitySelect = ui.qualitySelect ?? document.getElementById('qualitySelect');
  const statusDiv = ui.statusDiv ?? document.getElementById('status');

  if (!startBtn || !qualitySelect || !statusDiv) {
    return null;
  }

  startBtn.onclick = async () => {
    if (state.isStreaming) {
      await stopStream('stopped by user', startBtn, statusDiv);
      return;
    }

    if (state.isStarting) {
      return;
    }

    state.isAdaptiveRestartInProgress = false;
    state.qualityControlMode = qualitySelect.value;
    state.currentQualityMode = state.qualityControlMode === 'floor' ? 'floor' : 'high';
    state.activeProfile = null;
    await startStreaming({ isAdaptiveRestart: false }, { startBtn, qualitySelect, statusDiv });
  };

  qualitySelect.onchange = async () => {
    const selectedMode = qualitySelect.value;
    if (!['auto', 'high', 'floor'].includes(selectedMode)) {
      qualitySelect.value = state.qualityControlMode;
      return;
    }

    if (!state.isStreaming) {
      state.qualityControlMode = selectedMode;
      return;
    }

    if (state.isStarting || state.isAdaptiveRestartInProgress) {
      qualitySelect.value = state.qualityControlMode;
      return;
    }

    await applyQualityControlMode(selectedMode, qualitySelect);
  };

  qualitySelect.value = state.qualityControlMode;
  return { state, startBtn, qualitySelect, statusDiv };
}

initScreenShareApp();
