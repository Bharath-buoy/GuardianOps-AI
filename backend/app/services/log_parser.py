"""
Structured Log Parser
=======================
Parses raw application log lines into structured objects. Supports two
formats out of the box:

1. Plain-text lines:
   2026-07-22 10:15:32 [ERROR] payment-service: Database connection timeout
   2026-07-22 10:15:33 [WARN] auth-service: Retry attempt 2/3

2. JSON lines (one JSON object per line):
   {"timestamp": "...", "service": "...", "level": "ERROR", "message": "..."}

Multi-line stack traces (lines beginning with whitespace or "Traceback")
that immediately follow an ERROR line are attached to that entry.
"""
import json
import re
import uuid
from datetime import datetime, timezone

TEXT_LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\s*"
    r"\[(?P<level>[A-Z]+)\]\s*"
    r"(?:(?P<service>[\w\-.]+)\s*[:\-]\s*)?"
    r"(?P<message>.*)$"
)

VALID_LEVELS = {"DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"}

STACK_TRACE_START = re.compile(r"^Traceback \(most recent call last\):")
STACK_TRACE_CONTINUATION = re.compile(r"^(\s+|Caused by)")


def is_stack_trace_line(line: str) -> bool:
    """Kept for backwards compatibility / external callers: true if a line
    looks like the *start* of a traceback or an indented continuation of
    one. For batch parsing, `parse_log_batch` below uses a stateful
    tracker instead, since a single-line regex can't reliably tell "still
    inside a traceback" from "a new indented log line" without context."""
    return bool(STACK_TRACE_START.match(line) or STACK_TRACE_CONTINUATION.match(line))


def parse_log_batch(lines: list[str], default_service: str = "unknown-service") -> list[dict]:
    """
    Parse a batch of raw lines, attaching an entire multi-line stack trace
    (from "Traceback (most recent call last):" through its final indented
    "raise ..."/exception line) to the most recent ERROR entry — rather
    than guessing line-by-line, which misses the final exception line in
    most real Python/Java tracebacks.
    """
    entries: list[dict] = []
    in_traceback = False

    for line in lines:
        if not line.strip():
            in_traceback = False
            continue

        if STACK_TRACE_START.match(line) and entries and entries[-1]["level"] == "ERROR":
            in_traceback = True
            existing = entries[-1].get("stack_trace") or ""
            entries[-1]["stack_trace"] = (existing + "\n" + line.rstrip("\n")).strip()
            continue

        if in_traceback and STACK_TRACE_CONTINUATION.match(line):
            existing = entries[-1].get("stack_trace") or ""
            entries[-1]["stack_trace"] = (existing + "\n" + line.rstrip("\n")).strip()
            continue

        in_traceback = False
        parsed = parse_log_line(line, default_service=default_service)
        if parsed:
            entries.append(parsed)
    return entries


def _normalize_level(level: str) -> str:
    level = level.upper().strip()
    if level in ("WARNING",):
        return "WARN"
    if level in ("FATAL", "CRITICAL"):
        return "ERROR"
    if level not in VALID_LEVELS - {"WARNING", "FATAL", "CRITICAL"}:
        return "INFO"
    return level


def _normalize_timestamp(raw: str | None) -> str:
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    raw = raw.replace(",", ".").replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        return datetime.now(timezone.utc).isoformat()


def parse_log_line(line: str, default_service: str = "unknown-service") -> dict | None:
    """Parse a single raw log line into a structured entry, or None if blank."""
    line = line.rstrip("\n")
    if not line.strip():
        return None

    # --- JSON log format ---
    if line.strip().startswith("{"):
        try:
            obj = json.loads(line)
            return {
                "log_id": str(uuid.uuid4()),
                "service_id": obj.get("service") or obj.get("service_id") or default_service,
                "level": _normalize_level(str(obj.get("level", "INFO"))),
                "message": str(obj.get("message", "")),
                "timestamp": _normalize_timestamp(obj.get("timestamp")),
                "stack_trace": obj.get("stack_trace"),
                "source": "json",
            }
        except json.JSONDecodeError:
            pass  # fall through to text parsing

    # --- Plain-text log format ---
    match = TEXT_LOG_PATTERN.match(line)
    if match:
        groups = match.groupdict()
        return {
            "log_id": str(uuid.uuid4()),
            "service_id": groups.get("service") or default_service,
            "level": _normalize_level(groups["level"]),
            "message": groups["message"].strip(),
            "timestamp": _normalize_timestamp(groups.get("timestamp")),
            "stack_trace": None,
            "source": "text",
        }

    # --- Unstructured fallback (still captured, marked lower-confidence) ---
    return {
        "log_id": str(uuid.uuid4()),
        "service_id": default_service,
        "level": "INFO",
        "message": line.strip(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stack_trace": None,
        "source": "raw",
    }
