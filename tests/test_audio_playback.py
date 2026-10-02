import queue
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import audio_playback


def test_playback_falls_back_to_int16_when_float32_is_unsupported(monkeypatch):
    opened_dtypes = []
    written_chunks = []

    class FakeStream:
        def start(self):
            pass

        def write(self, samples):
            written_chunks.append(samples)

        def stop(self):
            pass

        def close(self):
            pass

    def open_output_stream(*, dtype, **_options):
        opened_dtypes.append(dtype)
        if dtype == "float32":
            raise RuntimeError("Sample format not supported [PaErrorCode -9994]")
        return FakeStream()

    service = audio_playback.AudioPlaybackService()
    service._sample_rate = 48000
    service._channels = 2
    service._running = True
    service._queue = queue.Queue()
    service._queue.put(np.array([[0.5, -0.5]], dtype=np.float32))
    service._queue.put(audio_playback._SENTINEL)

    monkeypatch.setattr(
        audio_playback,
        "sd",
        SimpleNamespace(OutputStream=open_output_stream),
    )
    monkeypatch.setattr(audio_playback.SCREEN_CAST, "AUDIO_PREBUFFER_FRAMES", 1)
    monkeypatch.setattr(audio_playback.logger, "exception", lambda *_args, **_kwargs: None)

    service._playback_loop()

    assert opened_dtypes == ["float32", "int32"]
    assert len(written_chunks) == 1
    assert written_chunks[0].dtype == np.int32
    np.testing.assert_array_equal(
        written_chunks[0],
        np.array([[1073741824, -1073741824]], dtype=np.int32),
    )


def test_playback_adapts_to_device_sample_rate_and_channels(monkeypatch):
    stream_options = []
    written_chunks = []

    class FakeStream:
        def start(self):
            pass

        def write(self, samples):
            written_chunks.append(samples)

        def stop(self):
            pass

        def close(self):
            pass

    def open_output_stream(*, dtype, **options):
        stream_options.append({"dtype": dtype, **options})
        return FakeStream()

    service = audio_playback.AudioPlaybackService()
    monkeypatch.setattr(
        audio_playback,
        "sd",
        SimpleNamespace(
            OutputStream=open_output_stream,
            query_devices=lambda **_options: {
                "default_samplerate": 44100,
                "max_output_channels": 1,
            },
        ),
    )
    monkeypatch.setattr(audio_playback.SCREEN_CAST, "AUDIO_PREBUFFER_FRAMES", 1)

    service._start_worker_locked(sample_rate=48000, channels=2)
    service._enqueue_samples(
        service._resample_samples(
            service._coerce_channels(np.array([[0.5, 0.5], [-0.5, -0.5]], dtype=np.float32))
        )
    )
    service._queue.put(audio_playback._SENTINEL)
    service._worker.join(timeout=1)

    assert stream_options[0]["samplerate"] == 44100
    assert stream_options[0]["channels"] == 1
    assert written_chunks[0].shape[1] == 1
    assert written_chunks[0].shape[0] == 2


def test_playback_retries_high_latency_when_low_latency_is_unsupported(monkeypatch):
    opened_latencies = []

    class FakeStream:
        def start(self):
            pass

        def write(self, _samples):
            pass

        def stop(self):
            pass

        def close(self):
            pass

    def open_output_stream(*, latency, **_options):
        opened_latencies.append(latency)
        if latency == "low":
            raise RuntimeError("Sample format not supported [PaErrorCode -9994]")
        return FakeStream()

    service = audio_playback.AudioPlaybackService()
    service._sample_rate = 48000
    service._channels = 2
    service._output_sample_rate = 48000
    service._output_channels = 2
    service._running = True
    service._queue = queue.Queue()
    service._queue.put(np.zeros((1, 2), dtype=np.float32))
    service._queue.put(audio_playback._SENTINEL)

    monkeypatch.setattr(
        audio_playback,
        "sd",
        SimpleNamespace(OutputStream=open_output_stream),
    )
    monkeypatch.setattr(audio_playback.SCREEN_CAST, "AUDIO_OUTPUT_LATENCY", "low")
    monkeypatch.setattr(audio_playback.SCREEN_CAST, "AUDIO_PREBUFFER_FRAMES", 1)

    service._playback_loop()

    assert opened_latencies[0] == "low"
    assert "high" in opened_latencies