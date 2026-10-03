"""Audio playback service for WebRTC screencast audio on Raspberry Pi.

This module accepts decoded aiortc audio frames and writes them to the system
audio output device (typically HDMI on Pi when configured as default).
"""

import asyncio
import queue
import subprocess
import threading
import time

try:
    import numpy as np
except Exception:  # pragma: no cover - environment-dependent import
    np = None

from globals import SCREEN_CAST
from app_logging import get_adapter


logger = get_adapter("audio", "audio")
_SENTINEL = object()


def log(message, **fields):
    logger.info(message, **fields)


class AudioPlaybackService:
    """Thread-backed audio sink for incoming aiortc AudioFrame objects.

    Design choices:
    - Playback runs on a dedicated thread so Qt/async loops stay responsive.
    - Queue is bounded and drops oldest frames under pressure to avoid unbound
      memory growth during short output stalls.
    - We tune for stability (higher output latency), matching the project goal
      for projector playback reliability over ultra-low latency.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._queue = None
        self._worker = None
        self._running = False
        self._sample_rate = None
        self._channels = None
        self._dropped_frames = 0
        self._trimmed_backlog_frames = 0
        self._last_overflow_log_at = 0.0

    def _reset_state_locked(self):
        self._queue = None
        self._worker = None
        self._running = False
        self._sample_rate = None
        self._channels = None
        self._dropped_frames = 0
        self._trimmed_backlog_frames = 0
        self._last_overflow_log_at = 0.0

    def _coerce_channels(self, interleaved_samples):
        if self._channels is None:
            return interleaved_samples

        input_channels = interleaved_samples.shape[1]
        if input_channels == self._channels:
            return interleaved_samples

        if self._channels == 1:
            return interleaved_samples.mean(axis=1, keepdims=True)

        if input_channels == 1:
            return interleaved_samples.repeat(self._channels, axis=1)

        if input_channels > self._channels:
            return interleaved_samples[:, : self._channels]

        missing = self._channels - input_channels
        zeros = np.zeros((interleaved_samples.shape[0], missing), dtype=interleaved_samples.dtype)
        return np.hstack((interleaved_samples, zeros))

    def _frame_to_samples(self, frame):
        # AudioFrame.to_ndarray() does not support the VideoFrame-style
        # format=... argument. We consume the native frame layout and normalize
        # to interleaved float32 samples for sounddevice.
        raw = frame.to_ndarray()
        if raw is None:
            raise ValueError("Audio frame produced no ndarray data")

        if raw.ndim == 1:
            interleaved = raw.reshape(-1, 1)
        else:
            format_info = getattr(frame, "format", None)
            is_planar = bool(getattr(format_info, "is_planar", False))

            channel_layout = getattr(frame, "layout", None)
            layout_channels = getattr(channel_layout, "channels", None)
            declared_channels = len(layout_channels) if layout_channels is not None else 0

            if is_planar:
                # Planar layout is [channels, samples]; convert to
                # sounddevice-friendly interleaved [samples, channels].
                interleaved = raw.T
            elif declared_channels > 0 and raw.shape[0] == 1:
                # Packed mono/stereo can arrive as a single row of interleaved
                # samples; reshape using declared channel count.
                interleaved = raw.reshape(-1, declared_channels)
            elif declared_channels > 0 and raw.shape[1] == declared_channels:
                interleaved = raw
            else:
                # Last-resort fallback for uncommon packed shapes.
                interleaved = raw.T if raw.shape[0] <= raw.shape[1] else raw

        if interleaved.ndim == 1:
            interleaved = interleaved.reshape(-1, 1)

        if interleaved.dtype != np.float32:
            if np.issubdtype(interleaved.dtype, np.integer):
                max_abs = max(abs(np.iinfo(interleaved.dtype).min), np.iinfo(interleaved.dtype).max)
                interleaved = interleaved.astype(np.float32) / float(max_abs)
            else:
                interleaved = interleaved.astype(np.float32)

        np.clip(interleaved, -1.0, 1.0, out=interleaved)
        return interleaved.copy(order="C"), int(interleaved.shape[1])

    def _enqueue_samples(self, samples):
        if self._queue is None:
            return

        try:
            self._queue.put_nowait(samples)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass

            self._dropped_frames += 1
            now = time.monotonic()
            if now - self._last_overflow_log_at >= 5:
                log(
                    "Playback queue overflow; dropping oldest buffered audio "
                    f"frames (dropped={self._dropped_frames})."
                )
                self._last_overflow_log_at = now

            try:
                self._queue.put_nowait(samples)
            except queue.Full:
                # If output thread is critically stalled, drop this frame too.
                self._dropped_frames += 1

        # Keep queue near real-time so audio does not drift behind the lower-
        # latency video path. If backlog grows, drop oldest audio chunks.
        target_frames = max(1, int(SCREEN_CAST.AUDIO_TARGET_QUEUE_FRAMES))
        while self._queue.qsize() > target_frames:
            try:
                self._queue.get_nowait()
                self._trimmed_backlog_frames += 1
            except queue.Empty:
                break

        now = time.monotonic()
        if self._trimmed_backlog_frames > 0 and now - self._last_overflow_log_at >= 5:
            log(
                "Trimmed buffered audio backlog to maintain A/V sync "
                f"(trimmed={self._trimmed_backlog_frames}, queue_size={self._queue.qsize()})."
            )
            self._last_overflow_log_at = now

    def _start_worker_locked(self, sample_rate, channels):
        if self._running:
            return

        max_frames = max(2, int(SCREEN_CAST.AUDIO_QUEUE_MAX_FRAMES))
        self._queue = queue.Queue(maxsize=max_frames)
        self._sample_rate = int(sample_rate)
        self._channels = int(channels)
        self._running = True

        self._worker = threading.Thread(target=self._playback_loop, daemon=True)
        self._worker.start()
        log(
            "Audio playback worker started "
            f"(sample_rate={self._sample_rate}, channels={self._channels}, "
            f"queue_max_frames={max_frames})."
        )

    def _build_aplay_command(self):
        command = [
            "aplay",
            "-q",
            "-D",
            SCREEN_CAST.AUDIO_ALSA_DEVICE,
            "-t",
            "raw",
            "-f",
            "S16_LE",
            "-c",
            str(self._channels),
            "-r",
            str(self._sample_rate),
        ]

        buffer_time_us = int(getattr(SCREEN_CAST, "AUDIO_ALSA_BUFFER_TIME_US", 0) or 0)
        period_time_us = int(getattr(SCREEN_CAST, "AUDIO_ALSA_PERIOD_TIME_US", 0) or 0)
        if buffer_time_us > 0:
            command.extend(["--buffer-time", str(buffer_time_us)])
        if period_time_us > 0:
            command.extend(["--period-time", str(period_time_us)])
        return command

    def submit_frame(self, frame):
        if not SCREEN_CAST.AUDIO_ENABLED:
            return

        if np is None:
            return

        try:
            samples, channels = self._frame_to_samples(frame)
        except Exception as exc:
            log(f"Failed to convert audio frame: {exc}")
            return

        sample_rate = int(getattr(frame, "sample_rate", 0) or 0)
        if sample_rate <= 0:
            log("Skipping audio frame with invalid sample rate.")
            return

        with self._lock:
            if not self._running:
                self._start_worker_locked(sample_rate=sample_rate, channels=channels)

            if sample_rate != self._sample_rate:
                # Keep stream configuration stable per session to avoid crackle
                # from teardown/re-open churn if sender briefly changes rate.
                log(
                    "Dropping audio frame due to sample-rate mismatch "
                    f"(incoming={sample_rate}, expected={self._sample_rate})."
                )
                return

            samples = self._coerce_channels(samples)
            self._enqueue_samples(samples)

    def _playback_loop(self):
        playback_process = None
        try:
            playback_process = subprocess.Popen(
                self._build_aplay_command(),
                stdin=subprocess.PIPE,
            )
            playback_stdin = playback_process.stdin
            if playback_stdin is None:
                raise RuntimeError("aplay stdin pipe was not created")
            log(
                "Audio playback process started "
                f"(device={SCREEN_CAST.AUDIO_ALSA_DEVICE}, sample_rate={self._sample_rate}, "
                f"channels={self._channels})."
            )

            prebuffer_frames = max(1, int(SCREEN_CAST.AUDIO_PREBUFFER_FRAMES))
            buffered = []
            prebuffering = True
            first_write_started_at = time.monotonic()

            while True:
                if self._queue is None:
                    break

                try:
                    chunk = self._queue.get(timeout=0.25)
                except queue.Empty:
                    if not self._running:
                        break
                    continue

                if chunk is _SENTINEL:
                    break

                if prebuffering:
                    buffered.append(chunk)
                    if len(buffered) < prebuffer_frames:
                        continue

                    for pending in buffered:
                        playback_stdin.write(self._samples_to_s16(pending).tobytes())
                    buffered.clear()
                    prebuffering = False
                    log(
                        "First audio samples written to playback device.",
                        startup_buffer_frames=prebuffer_frames,
                        startup_wait_ms=round((time.monotonic() - first_write_started_at) * 1000),
                    )
                    continue

                playback_stdin.write(self._samples_to_s16(chunk).tobytes())
        except Exception as exc:
            log(f"Audio playback loop failed: {exc}")
        finally:
            if playback_process is not None:
                try:
                    if playback_process.stdin is not None:
                        playback_process.stdin.close()
                except Exception:
                    pass
                try:
                    playback_process.wait(timeout=2)
                except Exception:
                    playback_process.terminate()

    def _samples_to_s16(self, samples):
        return np.rint(np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)

    async def stop(self):
        if np is None:
            return

        worker = None

        with self._lock:
            if not self._running:
                return

            self._running = False
            if self._queue is not None:
                try:
                    self._queue.put_nowait(_SENTINEL)
                except queue.Full:
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        self._queue.put_nowait(_SENTINEL)
                    except queue.Full:
                        pass

            worker = self._worker

        if worker is not None:
            await asyncio.to_thread(worker.join, 2)

        with self._lock:
            self._reset_state_locked()

        log("Audio playback worker stopped.")


audioPlayback = AudioPlaybackService()


def submitAudioFrame(frame):
    audioPlayback.submit_frame(frame)


async def stopAudioPlayback():
    await audioPlayback.stop()
