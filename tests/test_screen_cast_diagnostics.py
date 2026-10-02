import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import app_logging
import webserver.screen_cast as screen_cast


class FakePeer:
    connectionState = "connected"
    iceConnectionState = "connected"
    iceGatheringState = "complete"
    signalingState = "stable"


class FakeTrack:
    kind = "video"


class FakeReceiver:
    def __init__(self, track):
        self.track = track
        self._RTCRtpReceiver__active_ssrc = {1234: object()}
        self.pli_ssrcs = []

    async def _send_rtcp_pli(self, media_ssrc):
        self.pli_ssrcs.append(media_ssrc)


class FakePeerWithReceiver(FakePeer):
    def __init__(self, receiver):
        self.receiver = receiver

    def getReceivers(self):
        return [self.receiver]


def test_stream_exception_logs_type_traceback_and_peer_state(monkeypatch):
    app_logger = app_logging.AppLogger()
    monkeypatch.setattr(
        screen_cast,
        "logger",
        app_logging.LoggerAdapter(app_logger, "screencast", "screencast"),
    )

    exception = RuntimeError()
    screen_cast._log_stream_exception(
        FakePeer(),
        "Video stream reader ended with an exception.",
        exception,
        track_kind="video",
        frame_count=865,
    )

    record = app_logger.history()[0]
    assert record.level == "ERROR"
    assert record.fields["exception_type"] == "RuntimeError"
    assert record.fields["exception_message"] == ""
    assert "RuntimeError" in record.fields["traceback"]
    assert record.fields["track_kind"] == "video"
    assert record.fields["frame_count"] == 865
    assert record.fields["connection_state"] == "connected"
    assert record.fields["ice_connection_state"] == "connected"
    assert record.fields["signaling_state"] == "stable"


def test_closed_peer_media_stream_end_is_a_structured_warning(monkeypatch):
    app_logger = app_logging.AppLogger()
    monkeypatch.setattr(
        screen_cast,
        "logger",
        app_logging.LoggerAdapter(app_logger, "screencast", "screencast"),
    )

    class MediaStreamError(Exception):
        pass

    peer = FakePeer()
    peer.connectionState = "closed"
    screen_cast._log_stream_exception(
        peer,
        "Audio stream reader ended with an exception.",
        MediaStreamError(),
        track_kind="audio",
        frame_count=4486,
    )

    record = app_logger.history()[0]
    assert record.level == "WARNING"
    assert record.fields["exception_type"] == "MediaStreamError"
    assert record.fields["exception_message"] == ""
    assert record.fields["track_kind"] == "audio"
    assert record.fields["connection_state"] == "closed"


@pytest.mark.asyncio
async def test_request_keyframe_sends_pli_without_closing_peer(monkeypatch):
    monkeypatch.setattr(screen_cast.SCREEN_CAST, "KEYFRAME_REQUEST_MAX_PER_WINDOW", 3)
    monkeypatch.setattr(screen_cast.SCREEN_CAST, "KEYFRAME_REQUEST_WINDOW_SECONDS", 60)

    track = FakeTrack()
    receiver = FakeReceiver(track)
    peer = FakePeerWithReceiver(receiver)
    request_times = []

    requested = await screen_cast._request_keyframe(
        peer, track, "test recovery", request_times
    )

    assert requested is True
    assert receiver.pli_ssrcs == [1234]
    assert peer.connectionState == "connected"
    assert len(request_times) == 1


@pytest.mark.asyncio
async def test_request_keyframe_obeys_rate_limit(monkeypatch):
    monkeypatch.setattr(screen_cast.SCREEN_CAST, "KEYFRAME_REQUEST_MAX_PER_WINDOW", 1)
    monkeypatch.setattr(screen_cast.SCREEN_CAST, "KEYFRAME_REQUEST_WINDOW_SECONDS", 60)

    track = FakeTrack()
    receiver = FakeReceiver(track)
    peer = FakePeerWithReceiver(receiver)
    request_times = []

    assert await screen_cast._request_keyframe(peer, track, "first", request_times)
    assert not await screen_cast._request_keyframe(peer, track, "limited", request_times)
    assert receiver.pli_ssrcs == [1234]