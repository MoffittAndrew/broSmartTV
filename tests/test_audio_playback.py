import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import audio_playback


def test_build_aplay_command_includes_low_latency_parameters(monkeypatch):
    service = audio_playback.AudioPlaybackService()
    service._channels = 2
    service._sample_rate = 48_000

    monkeypatch.setattr(audio_playback.SCREEN_CAST, "AUDIO_ALSA_DEVICE", "hw:0,0")
    monkeypatch.setattr(audio_playback.SCREEN_CAST, "AUDIO_ALSA_BUFFER_TIME_US", 80_000)
    monkeypatch.setattr(audio_playback.SCREEN_CAST, "AUDIO_ALSA_PERIOD_TIME_US", 20_000)

    assert service._build_aplay_command() == [
        "aplay",
        "-q",
        "-D",
        "hw:0,0",
        "-t",
        "raw",
        "-f",
        "S16_LE",
        "-c",
        "2",
        "-r",
        "48000",
        "--buffer-time",
        "80000",
        "--period-time",
        "20000",
    ]


def test_build_aplay_command_omits_disabled_latency_parameters(monkeypatch):
    service = audio_playback.AudioPlaybackService()
    service._channels = 2
    service._sample_rate = 48_000

    monkeypatch.setattr(audio_playback.SCREEN_CAST, "AUDIO_ALSA_BUFFER_TIME_US", 0)
    monkeypatch.setattr(audio_playback.SCREEN_CAST, "AUDIO_ALSA_PERIOD_TIME_US", 0)

    command = service._build_aplay_command()

    assert "--buffer-time" not in command
    assert "--period-time" not in command