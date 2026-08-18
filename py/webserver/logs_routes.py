"""Web routes for live and historical structured application logs.

The module is intentionally independent of the full screen-cast stack so it
can be registered by the standby server before Qt and aiortc are loaded.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Iterable

from aiohttp import web

from app_logging import LogRecord, get_log_dir, get_logger


WEBPAGES_DIR = Path(__file__).resolve().parents[2] / "webpages"
SESSION_FILE_PATTERN = re.compile(r"^session-[A-Za-z0-9TzZ-]+\.jsonl$")
MAX_RECORDS = 1000
MAX_FILE_RECORDS = 5000
MAX_SSE_QUEUE = 200
SHUTDOWN_KEY = "logs_stream_shutdown"
KNOWN_CATEGORIES = {
    "audio",
    "gui",
    "projector",
    "remote",
    "screencast",
    "startup",
    "standby",
    "teardown",
    "update",
    "webhosting",
    "wifi",
}
KNOWN_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
KNOWN_SOURCES = {
    "audio",
    "gui",
    "ir",
    "launcher",
    "main",
    "remote",
    "remote_control",
    "screencast",
    "standby",
    "teardown",
    "webserver",
    "wifi",
}


def _query_values(request: web.Request, name: str) -> set[str] | None:
    values = request.rel_url.query.getall(name, [])
    if not values:
        return None

    result = set()
    for value in values:
        result.update(item.strip() for item in value.split(",") if item.strip())
    return result or None


def _record_matches(
    record: LogRecord | dict,
    *,
    levels: Iterable[str] | None = None,
    sources: Iterable[str] | None = None,
    categories: Iterable[str] | None = None,
) -> bool:
    level_set = {level.upper() for level in levels} if levels is not None else None
    source_set = set(sources) if sources is not None else None
    category_set = set(categories) if categories is not None else None
    level = record.level if isinstance(record, LogRecord) else str(record.get("level", "")).upper()
    source = record.source if isinstance(record, LogRecord) else str(record.get("source", ""))
    category = record.category if isinstance(record, LogRecord) else str(record.get("category", ""))
    return (
        (level_set is None or level in level_set)
        and (source_set is None or source in source_set)
        and (category_set is None or category in category_set)
    )


def _record_dict(record: LogRecord | dict) -> dict:
    return record.to_dict() if isinstance(record, LogRecord) else record


def _filtered_records(records, request: web.Request, limit: int = MAX_RECORDS) -> list[dict]:
    levels = _query_values(request, "level")
    sources = _query_values(request, "source")
    categories = _query_values(request, "category")
    return [
        _record_dict(record)
        for record in records
        if _record_matches(record, levels=levels, sources=sources, categories=categories)
    ][-limit:]


def _safe_log_dir() -> Path:
    return get_log_dir().resolve()


def _safe_session_path(filename: str) -> Path:
    if not SESSION_FILE_PATTERN.fullmatch(filename) or Path(filename).name != filename:
        raise web.HTTPBadRequest(text="Invalid session filename")

    root = _safe_log_dir()
    target = (root / filename).resolve()
    if target.parent != root or not target.is_file():
        raise web.HTTPNotFound(text="Session log not found")
    return target


def _read_session_records(path: Path) -> list[dict]:
    records = []
    try:
        with path.open("r", encoding="utf-8") as log_file:
            for line_number, line in enumerate(log_file):
                if line_number >= MAX_FILE_RECORDS:
                    break
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if isinstance(record, dict):
                    records.append(record)
    except OSError:
        raise web.HTTPNotFound(text="Session log not found")
    return records


async def logs_page(request: web.Request) -> web.FileResponse:
    return web.FileResponse(WEBPAGES_DIR / "logs.html")


async def current_history(request: web.Request) -> web.Response:
    records = get_logger().history()
    return web.json_response({"records": _filtered_records(records, request)})


async def filter_options(request: web.Request) -> web.Response:
    """Return filter values from current history and available session files."""
    records = [record.to_dict() for record in get_logger().history()]
    root = _safe_log_dir()
    if root.exists():
        for path in root.iterdir():
            if path.is_file() and SESSION_FILE_PATTERN.fullmatch(path.name):
                records.extend(_read_session_records(path)[-MAX_RECORDS:])

    return web.json_response({
        "categories": sorted(KNOWN_CATEGORIES | {record.get("category", "") for record in records if record.get("category")}),
        "levels": sorted(KNOWN_LEVELS | {str(record.get("level", "")).upper() for record in records if record.get("level")}),
        "sources": sorted(KNOWN_SOURCES | {record.get("source", "") for record in records if record.get("source")}),
    })


async def list_sessions(request: web.Request) -> web.Response:
    root = _safe_log_dir()
    if not root.exists():
        return web.json_response({"files": []})

    files = []
    for path in root.iterdir():
        if not path.is_file() or not SESSION_FILE_PATTERN.fullmatch(path.name):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        files.append({
            "filename": path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        })
    files.sort(key=lambda item: item["modified"], reverse=True)
    return web.json_response({"files": files})


async def session_history(request: web.Request) -> web.Response:
    records = _read_session_records(_safe_session_path(request.match_info["filename"]))
    return web.json_response({"filename": request.match_info["filename"], "records": _filtered_records(records, request, MAX_RECORDS)})


async def log_stream(request: web.Request) -> web.StreamResponse:
    logger = get_logger()
    queue: asyncio.Queue[LogRecord] = asyncio.Queue(maxsize=MAX_SSE_QUEUE)
    loop = asyncio.get_running_loop()
    shutdown_event = request.app[SHUTDOWN_KEY]
    unsubscribe = None

    def enqueue(record: LogRecord) -> None:
        def put_record() -> None:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(record)

        try:
            loop.call_soon_threadsafe(put_record)
        except RuntimeError:
            pass

    response = web.StreamResponse(
        status=200,
        headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
    await response.prepare(request)
    filters = {
        "levels": _query_values(request, "level"),
        "sources": _query_values(request, "source"),
        "categories": _query_values(request, "category"),
    }

    try:
        for record in _filtered_records(logger.history(), request):
            await response.write(f"data: {json.dumps(record, ensure_ascii=True)}\n\n".encode())

        unsubscribe = logger.subscribe(
            enqueue,
            levels=filters["levels"],
            sources=filters["sources"],
            categories=filters["categories"],
        )
        try:
            while True:
                queue_task = asyncio.create_task(queue.get())
                shutdown_task = asyncio.create_task(shutdown_event.wait())
                done, pending = await asyncio.wait(
                    (queue_task, shutdown_task),
                    timeout=15,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()

                if shutdown_task in done:
                    break
                if queue_task in done:
                    record = queue_task.result()
                    await response.write(f"data: {json.dumps(record.to_dict(), ensure_ascii=True)}\n\n".encode())
                else:
                    await response.write(b": keep-alive\n\n")
        finally:
            unsubscribe()
    except (asyncio.CancelledError, ConnectionResetError, RuntimeError):
        if unsubscribe is not None:
            unsubscribe()
    finally:
        if not response._eof_sent:
            try:
                await response.write_eof()
            except (ConnectionResetError, RuntimeError):
                pass
    return response


def add_routes(application: web.Application) -> None:
    """Register logs page, replay, historical, and live-stream routes."""
    application[SHUTDOWN_KEY] = asyncio.Event()

    async def stop_streams(_application):
        application[SHUTDOWN_KEY].set()

    application.on_shutdown.append(stop_streams)
    application.router.add_get("/logs", logs_page)
    application.router.add_get("/logs/api/history", current_history)
    application.router.add_get("/logs/api/options", filter_options)
    application.router.add_get("/logs/api/files", list_sessions)
    application.router.add_get("/logs/api/files/{filename}", session_history)
    application.router.add_get("/logs/api/stream", log_stream)


def reset_stream_shutdown(application: web.Application) -> None:
    """Allow a shared application object to be started again after cleanup."""
    application[SHUTDOWN_KEY].clear()