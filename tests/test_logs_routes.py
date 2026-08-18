import json
import sys
from pathlib import Path

import pytest
from aiohttp.test_utils import make_mocked_request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import app_logging
import webserver.logs_routes as logs_routes


def _request(path, **match_info):
    request = make_mocked_request("GET", path)
    request.match_info.update(match_info)
    return request


@pytest.mark.asyncio
async def test_current_history_supports_multiple_filters(monkeypatch):
    logger = app_logging.AppLogger()
    logger.emit("info", "cast", source="screen", category="screencast")
    logger.emit("warning", "gui", source="window", category="gui")
    logger.emit("error", "remote", source="remote", category="remote")
    monkeypatch.setattr(logs_routes, "get_logger", lambda: logger)

    response = await logs_routes.current_history(_request("/logs/api/history?category=screencast&category=gui&level=INFO,WARNING"))
    payload = json.loads(response.body)

    assert [record["message"] for record in payload["records"]] == ["cast", "gui"]


@pytest.mark.asyncio
async def test_historical_records_ignore_malformed_lines_and_reject_unsafe_names(monkeypatch, tmp_path):
    session_path = tmp_path / "session-20260818T000000Z-test.jsonl"
    session_path.write_text(
        json.dumps({"level": "ERROR", "category": "gui", "message": "failed"})
        + "\nnot json\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(logs_routes, "get_log_dir", lambda: tmp_path)

    response = await logs_routes.session_history(
        _request(
            "/logs/api/files/session-20260818T000000Z-test.jsonl?category=gui",
            filename="session-20260818T000000Z-test.jsonl",
        )
    )
    assert len(json.loads(response.body)["records"]) == 1

    with pytest.raises(Exception) as error:
        await logs_routes.session_history(
            _request("/logs/api/files/..%2Fsecret.jsonl", filename="../secret.jsonl")
        )
    assert getattr(error.value, "status", None) in {400, 404}


@pytest.mark.asyncio
async def test_list_sessions_only_returns_session_files(monkeypatch, tmp_path):
    (tmp_path / "session-20260818T000000Z-test.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "other.txt").write_text("secret", encoding="utf-8")
    monkeypatch.setattr(logs_routes, "get_log_dir", lambda: tmp_path)

    response = await logs_routes.list_sessions(_request("/logs/api/files"))
    assert [item["filename"] for item in json.loads(response.body)["files"]] == [
        "session-20260818T000000Z-test.jsonl"
    ]