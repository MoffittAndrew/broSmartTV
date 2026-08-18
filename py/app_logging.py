"""Process-wide structured application logging.

This module intentionally has no Qt, aiohttp, or Raspberry Pi-specific imports
so it can be initialized before either application startup path begins.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from threading import RLock
from typing import Callable, Iterable, Mapping
from uuid import uuid4


_REDACTION_PATTERNS = (
    re.compile(r"(?i)(password|passwd|token|secret|authorization|api[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)(sdp)\s*[:=]\s*.+"),
)


@dataclass(frozen=True)
class LogRecord:
    """A serializable event that can be stored, displayed, or streamed later."""

    timestamp: str
    level: str
    source: str
    category: str
    message: str
    session_id: str
    fields: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _redact_text(message: str) -> str:
    redacted = message
    for pattern in _REDACTION_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}=<redacted>", redacted)
    return redacted


def _redact_fields(fields: Mapping[str, object]) -> dict[str, object]:
    safe_fields: dict[str, object] = {}
    for key, value in fields.items():
        if re.search(r"(?i)(password|passwd|token|secret|authorization|api[_-]?key|sdp)", key):
            safe_fields[key] = "<redacted>"
        elif isinstance(value, str):
            safe_fields[key] = _redact_text(value)
        else:
            safe_fields[key] = value
    return safe_fields


def _default_log_dir() -> Path:
    configured_dir = os.getenv("BRO_LOG_DIR")
    if configured_dir:
        return Path(configured_dir)

    model_path = Path("/proc/device-tree/model")
    if model_path.exists():
        try:
            if "raspberry pi" in model_path.read_text(errors="ignore").lower():
                return Path("/bro/var/log")
        except OSError:
            pass

    return Path(__file__).resolve().parents[1] / "logs"


def _matches(value: str, accepted: Iterable[str] | None) -> bool:
    return accepted is None or value in accepted


class AppLogger:
    """Thread-safe event store with stdout and per-session file sinks."""

    def __init__(self, history_size: int = 1000):
        self.session_id = uuid4().hex
        self._history: deque[LogRecord] = deque(maxlen=history_size)
        self._subscribers: dict[int, Callable[[LogRecord], None]] = {}
        self._next_subscriber_id = 0
        self._lock = RLock()
        self._file = None
        self._log_dir: Path | None = None

    def configure_file(self, log_dir: str | os.PathLike[str] | None = None) -> Path:
        """Open this session's file once and return its path."""
        with self._lock:
            if self._file is not None:
                return self._log_dir / self._file.name  # type: ignore[union-attr]

            self._log_dir = Path(log_dir) if log_dir is not None else _default_log_dir()
            self._log_dir.mkdir(parents=True, exist_ok=True)
            filename = f"session-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{self.session_id}.jsonl"
            self._file = (self._log_dir / filename).open("a", encoding="utf-8")
            return self._log_dir / filename

    def subscribe(
        self,
        callback: Callable[[LogRecord], None],
        *,
        levels: Iterable[str] | None = None,
        sources: Iterable[str] | None = None,
        categories: Iterable[str] | None = None,
    ) -> Callable[[], None]:
        level_set = {level.upper() for level in levels} if levels is not None else None
        source_set = set(sources) if sources is not None else None
        category_set = set(categories) if categories is not None else None

        def filtered_callback(record: LogRecord) -> None:
            if (
                _matches(record.level, level_set)
                and _matches(record.source, source_set)
                and _matches(record.category, category_set)
            ):
                callback(record)

        with self._lock:
            subscriber_id = self._next_subscriber_id
            self._next_subscriber_id += 1
            self._subscribers[subscriber_id] = filtered_callback

        def unsubscribe() -> None:
            with self._lock:
                self._subscribers.pop(subscriber_id, None)

        return unsubscribe

    def emit(
        self,
        level: str,
        message: object,
        *,
        source: str,
        category: str,
        fields: Mapping[str, object] | None = None,
    ) -> LogRecord:
        record = LogRecord(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            level=level.upper(),
            source=source,
            category=category,
            message=_redact_text(str(message)),
            session_id=self.session_id,
            fields=_redact_fields(fields or {}),
        )

        with self._lock:
            self._history.append(record)
            subscribers = tuple(self._subscribers.values())
            output = json.dumps(record.to_dict(), ensure_ascii=True, separators=(",", ":"))
            if self._file is not None:
                self._file.write(output + "\n")
                self._file.flush()

        print(self.format(record), file=sys.stderr if record.level in {"ERROR", "CRITICAL"} else sys.stdout)
        for callback in subscribers:
            try:
                callback(record)
            except Exception:
                # Observers must never be able to break the application logger.
                continue
        return record

    def history(
        self,
        *,
        levels: Iterable[str] | None = None,
        sources: Iterable[str] | None = None,
        categories: Iterable[str] | None = None,
    ) -> list[LogRecord]:
        level_set = {level.upper() for level in levels} if levels is not None else None
        source_set = set(sources) if sources is not None else None
        category_set = set(categories) if categories is not None else None
        with self._lock:
            return [
                record
                for record in self._history
                if _matches(record.level, level_set)
                and _matches(record.source, source_set)
                and _matches(record.category, category_set)
            ]

    @staticmethod
    def format(record: LogRecord) -> str:
        return (
            f"{record.timestamp} [{record.level}] "
            f"[{record.source}:{record.category}] {record.message}"
        )

    def close(self) -> None:
        with self._lock:
            if self._file is not None:
                self._file.close()
                self._file = None


class LoggerAdapter:
    """Small module-facing facade that supplies source and category."""

    def __init__(self, logger: AppLogger, source: str, category: str):
        self._logger = logger
        self.source = source
        self.category = category

    def log(
        self,
        level: str,
        message: object,
        *,
        category: str | None = None,
        **fields: object,
    ) -> LogRecord:
        return self._logger.emit(
            level,
            message,
            source=self.source,
            category=category or self.category,
            fields=fields,
        )

    def debug(self, message: object, *, category: str | None = None, **fields: object) -> LogRecord:
        return self.log("DEBUG", message, category=category, **fields)

    def info(self, message: object, *, category: str | None = None, **fields: object) -> LogRecord:
        return self.log("INFO", message, category=category, **fields)

    def warning(self, message: object, *, category: str | None = None, **fields: object) -> LogRecord:
        return self.log("WARNING", message, category=category, **fields)

    def error(self, message: object, *, category: str | None = None, **fields: object) -> LogRecord:
        return self.log("ERROR", message, category=category, **fields)


_app_logger: AppLogger | None = None


def get_logger(*, history_size: int = 1000, log_dir: str | os.PathLike[str] | None = None) -> AppLogger:
    """Return the process-wide logger, configuring its file sink once."""
    global _app_logger
    if _app_logger is None:
        _app_logger = AppLogger(history_size=history_size)
    _app_logger.configure_file(log_dir)
    return _app_logger


def get_adapter(source: str, category: str, **kwargs: object) -> LoggerAdapter:
    return LoggerAdapter(get_logger(**kwargs), source, category)


def reset_logger() -> None:
    """Close and clear the singleton for tests or a deliberate process reset."""
    global _app_logger
    if _app_logger is not None:
        _app_logger.close()
    _app_logger = None