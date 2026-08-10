"""Audio playback service for WebRTC screencast audio on Raspberry Pi.

This module accepts decoded aiortc audio frames and writes them to the system
audio output device (typically HDMI on Pi when configured as default).
"""

import asyncio
import queue
import threading
import time

try:
    import numpy as np
except Exception:  # pragma: no cover - environment-dependent import
    np = None

try:
    import sounddevice as sd
except Exception:  # pragma: no cover - environment-dependent import
    sd = None

from globals import SCREEN_CAST


LOG_PREFIX = "[screencast-audio]"
_SENTINEL = object()


def log(message):
    print(f"{LOG_PREFIX} {message}")


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
        self._last_overflow_log_at = 0.0

    def _reset_state_locked(self):
        self._queue = None
        self._worker = None
        self._running = False
        self._sample_rate = None
        self._channels = None
        self._dropped_frames = 0
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
        planar = frame.to_ndarray(format="fltp")

        if planar.ndim == 1:
            planar = planar.reshape(1, -1)

        channels = int(planar.shape[0])
        interleaved = planar.T.copy(order="C")
        if interleaved.ndim == 1:
            interleaved = interleaved.reshape(-1, 1)

        return interleaved, channels

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

    def _start_worker_locked(self, sample_rate, channels):
        if self._running:
            return

        max_frames = max(10, int(SCREEN_CAST.AUDIO_QUEUE_MAX_FRAMES))
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

    def submit_frame(self, frame):
        if not SCREEN_CAST.AUDIO_ENABLED:
            return

        if sd is None or np is None:
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
        stream = None
        try:
            stream = sd.OutputStream(
                samplerate=self._sample_rate,
                channels=self._channels,
                dtype="float32",
                latency="high",
                device=SCREEN_CAST.AUDIO_OUTPUT_DEVICE,
            )
            stream.start()

            prebuffer_frames = max(1, int(SCREEN_CAST.AUDIO_PREBUFFER_FRAMES))
            buffered = []

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

                if len(buffered) < prebuffer_frames:
                    buffered.append(chunk)
                    continue

                if buffered:
                    for pending in buffered:
                        stream.write(pending)
                    buffered.clear()

                stream.write(chunk)
        except Exception as exc:
            log(f"Audio playback loop failed: {exc}")
        finally:
            if stream is not None:
                try:
                    stream.stop()
                except Exception:
                    pass
                try:
                    stream.close()
                except Exception:
                    pass

    async def stop(self):
        if sd is None or np is None:
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
