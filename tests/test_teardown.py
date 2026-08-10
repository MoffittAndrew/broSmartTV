import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'py'))

import teardown


class FakeProjector:
    def __init__(self):
        self.off_calls = 0

    async def off(self):
        self.off_calls += 1


@pytest.mark.asyncio
async def test_teardown_app_stops_server_and_quits(monkeypatch):
    stop_called = False
    stop_audio_called = False
    quit_called = False

    async def fake_stop_screen_cast_server():
        nonlocal stop_called
        stop_called = True

    async def fake_stop_audio_playback():
        nonlocal stop_audio_called
        stop_audio_called = True

    class FakeQCoreApplication:
        @staticmethod
        def quit():
            nonlocal quit_called
            quit_called = True

    monkeypatch.setattr(teardown, 'stopScreenCastServer', fake_stop_screen_cast_server)
    monkeypatch.setattr(teardown, 'stopAudioPlayback', fake_stop_audio_playback)
    monkeypatch.setattr(teardown, 'QCoreApplication', FakeQCoreApplication)

    teardown.reset_shutdown_state()
    projector = FakeProjector()
    await teardown.teardown_app(projector_interface=projector, quit_app=True)

    assert projector.off_calls == 1
    assert stop_audio_called is True
    assert stop_called is True
    assert quit_called is True


@pytest.mark.asyncio
async def test_teardown_app_is_idempotent(monkeypatch):
    stop_calls = 0
    stop_audio_calls = 0
    off_calls = 0

    async def fake_stop_screen_cast_server():
        nonlocal stop_calls
        stop_calls += 1

    async def fake_stop_audio_playback():
        nonlocal stop_audio_calls
        stop_audio_calls += 1

    class FakeProjector:
        async def off(self):
            nonlocal off_calls
            off_calls += 1

    monkeypatch.setattr(teardown, 'stopScreenCastServer', fake_stop_screen_cast_server)
    monkeypatch.setattr(teardown, 'stopAudioPlayback', fake_stop_audio_playback)
    monkeypatch.setattr(teardown, 'QCoreApplication', type('FakeQCoreApplication', (), {'quit': staticmethod(lambda: None)}))

    teardown.reset_shutdown_state()
    projector = FakeProjector()
    await teardown.teardown_app(projector_interface=projector)
    await teardown.teardown_app(projector_interface=projector)

    assert off_calls == 1
    assert stop_audio_calls == 1
    assert stop_calls == 1
