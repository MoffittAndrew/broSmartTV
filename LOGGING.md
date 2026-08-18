# Application logging

The smart TV uses one process-wide structured logger. Application code emits records through `broSmartTV/py/app_logging.py`; the logger writes a session JSONL file, keeps a bounded in-memory history, prints a human-readable line to the process output, and notifies subscribers such as the Qt launch screen and the logs webpage stream.

## Startup model

There are two application startup paths:

- Raspberry Pi startup begins in `py/launch.py`. The logger is initialized before the lightweight standby server starts, so standby diagnostics and the `/logs` page can work before Qt, aiortc, or the main UI are loaded.
- Local development starts in `py/main.py`. It initializes or reuses the same process-wide logger before the application wiring begins.

`get_logger()` is idempotent. Repeated imports or calls reuse the same logger and do not open duplicate session files. The logger must remain dependency-light: do not add PyQt, aiohttp, aiortc, audio, or UI imports to `app_logging.py`.

## Record format

Each `LogRecord` contains:

| Field | Meaning |
| --- | --- |
| `timestamp` | UTC ISO-8601 timestamp with millisecond precision |
| `level` | Uppercase severity such as `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| `source` | The subsystem or module emitting the event, such as `screencast`, `wifi`, or `launcher` |
| `category` | A filterable semantic group, such as `screencast`, `gui`, `startup`, `teardown`, `webhosting`, or `remote` |
| `message` | Human-readable event description |
| `session_id` | UUID-like identifier shared by all records from one process session |
| `fields` | Optional safe structured metadata |

Keep `source` and `category` separate. A source identifies ownership; a category describes the operational concern. Web consumers use both dimensions independently.

## Emitting records

Use an adapter at module scope:

```python
from app_logging import get_adapter

logger = get_adapter("wifi", "wifi")

logger.info("Wi-Fi connection requested", ssid=network.ssid)
logger.warning("Wi-Fi connection rejected", ssid=network.ssid)
logger.error("Wi-Fi command failed", return_code=result.returncode)
```

The adapter supplies the default source and category. A specific event can override only the category:

```python
logger.info("Starting screen cast server", category="screencast", port=443)
```

Use structured fields for safe metadata that a future webpage can display or query. Prefer counts, states, booleans, identifiers designed for display, and return codes. Do not put a complete command, request body, SDP, exception object, password, token, or credential into fields.

The adapter methods are:

- `debug(message, **fields)`
- `info(message, **fields)`
- `warning(message, **fields)`
- `error(message, **fields)`
- `log(level, message, category=None, **fields)`

## Redaction and privacy

Redaction happens before records are stored, printed, sent to subscribers, or exposed through the logs webpage. Keys containing `password`, `passwd`, `token`, `secret`, `authorization`, `api-key`, or `sdp` are replaced with `<redacted>`. Matching sensitive `key=value` text in messages is also redacted.

Redaction is a final guard, not a substitute for careful logging. Do not deliberately pass secrets and do not log raw `nmcli` output, raw HTTP request bodies, SDP, access tokens, or unrestricted exception payloads. If a new sensitive format is introduced, update `_REDACTION_PATTERNS` and `_redact_fields()` and add a regression test.

## Storage

Every process session gets one JSON Lines file named approximately:

```text
session-20260818T120000Z-<session-id>.jsonl
```

Each line is one JSON object matching the record format. Files are flushed after each event so a crash still leaves the latest records available. The logger creates the directory lazily when first initialized.

The directory is selected in this order:

1. `BRO_LOG_DIR`, when set.
2. `/bro/var/log` on a Raspberry Pi.
3. The project-local `broSmartTV/logs/` directory during local development.

The project-local directory is ignored by Git. On the Pi, prefer `/bro/var/log` because `/bro/app` is updated by the launcher and should not be the persistence boundary for diagnostics. The runtime user must have permission to create and append files in the selected directory.

`get_log_dir()` returns the selected directory without opening a file. Web routes use it to browse historical session files. Do not construct a second log path in a server module.

## History and subscribers

`AppLogger` keeps a bounded in-memory history, currently defaulting to 1,000 records. Use:

```python
records = get_logger().history(
    levels={"ERROR", "WARNING"},
    categories={"screencast", "gui"},
)
```

Filter values are ORed within one dimension and ANDed across dimensions. A subscriber callback can use the same filters:

```python
unsubscribe = get_logger().subscribe(
    callback,
    categories={"startup", "update"},
)

# Call this when the consumer is destroyed.
unsubscribe()
```

The logger copies the subscriber list before invoking callbacks. One failing subscriber is isolated and cannot stop the application from logging. Subscriber callbacks may run from asyncio tasks or worker threads, so they must not mutate Qt widgets directly. The launch screen forwards records through a Qt signal. Future network consumers should use a bounded queue and their event loop's thread-safe scheduling method.

## Web diagnostics

The CSS-agnostic `/logs` page is available in both awake and standby server modes. The page consumes:

- `GET /logs/api/history` for bounded current-session replay.
- `GET /logs/api/stream` for Server-Sent Events. It sends a replay, then live records.
- `GET /logs/api/files` for safe session-file metadata.
- `GET /logs/api/files/{filename}` for bounded historical records from a whitelisted session filename.

Filtering uses repeated or comma-separated `category`, `level`, and `source` query parameters. Multiple values within one parameter are ORed; different parameters are ANDed. For example:

```text
/logs/api/history?category=screencast&category=gui&level=ERROR,WARNING
```

The routes accept only the session filename convention and resolve paths before reading. They ignore malformed JSONL lines and bound replay/file responses. The standby server deliberately registers these routes before its fallback redirect, so `/logs` remains usable while `/cast` continues redirecting to `/standby`.

## Adding a new subsystem

1. Choose a stable source and category.
2. Create a module-level adapter with `get_adapter()`.
3. Emit safe structured records instead of `print()`.
4. Preserve existing rate limits for high-volume events such as frame statistics.
5. Add tests for important error paths and sensitive data handling.
6. If the event should be visible on the launch screen, use the existing `startup` or `update` category and keep UI delivery on the Qt thread.
7. If a future web consumer needs a new field, add it to the record contract and update the API/page tests.

## Operational checks

When diagnosing a deployment:

1. Confirm `BRO_LOG_DIR` and its permissions.
2. Confirm one new session file appears after starting the process.
3. Confirm records contain timestamps, source, category, level, and session ID.
4. Confirm the launch screen shows startup/update records.
5. Confirm `/logs` works before powering the TV on.
6. Inspect logs for secrets before sharing them.
7. Preserve the launcher contract: fatal Pi startup errors must still exit non-zero so the outer launcher can restart the process.
