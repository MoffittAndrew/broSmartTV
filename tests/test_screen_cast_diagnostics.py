import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import app_logging
import webserver.screen_cast as screen_cast


class FakePeer:
    connectionState = "connected"
    iceConnectionState = "connected"
    iceGatheringState = "complete"
    signalingState = "stable"


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