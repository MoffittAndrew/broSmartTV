import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import app_logging


def test_logger_writes_structured_session_file_and_redacts(tmp_path):
    logger = app_logging.AppLogger(history_size=3)
    log_path = logger.configure_file(tmp_path)

    record = logger.emit(
        "info",
        "Connecting with password=hunter2 and sdp=v=0",
        source="wifi",
        category="network",
        fields={"token": "secret-token", "attempt": 1},
    )
    logger.close()

    saved = json.loads(log_path.read_text(encoding="utf-8"))
    assert saved["session_id"] == record.session_id
    assert saved["source"] == "wifi"
    assert saved["category"] == "network"
    assert "hunter2" not in saved["message"]
    assert "secret-token" not in saved["fields"]["token"]
    assert record.timestamp.endswith("+00:00")


def test_history_filters_and_stays_bounded():
    logger = app_logging.AppLogger(history_size=2)
    logger.emit("info", "one", source="gui", category="startup")
    logger.emit("warning", "two", source="web", category="hosting")
    logger.emit("error", "three", source="gui", category="teardown")

    assert [record.message for record in logger.history()] == ["two", "three"]
    assert [record.message for record in logger.history(sources=["gui"])] == ["three"]
    assert [record.message for record in logger.history(levels=["ERROR"])] == ["three"]


def test_subscriber_can_be_removed_and_failures_are_isolated():
    logger = app_logging.AppLogger()
    received = []

    def broken_callback(record):
        raise RuntimeError("observer failed")

    unsubscribe = logger.subscribe(broken_callback)
    unsubscribe()
    logger.subscribe(received.append)
    logger.emit("info", "hello", source="test", category="unit")

    assert [record.message for record in received] == ["hello"]


def test_exception_logging_persists_full_traceback(tmp_path):
    logger = app_logging.AppLogger()
    log_path = logger.configure_file(tmp_path)

    def outer_call():
        return inner_call()

    def inner_call():
        raise AttributeError("missing callback")

    try:
        outer_call()
    except Exception as exc:
        record = app_logging.LoggerAdapter(logger, "launcher", "startup").exception(
            "Launcher exception",
            exc,
        )
    logger.close()

    saved = json.loads(log_path.read_text(encoding="utf-8"))
    assert record.fields["exception_type"] == "AttributeError"
    assert "AttributeError: missing callback" in record.fields["traceback"]
    assert "outer_call" in record.fields["traceback"]
    assert "inner_call" in saved["fields"]["traceback"]