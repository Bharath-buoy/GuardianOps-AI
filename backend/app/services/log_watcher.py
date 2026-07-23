"""
Real-Time Log File Watcher
============================
Uses `watchdog` to monitor a logs directory for file changes and tails new
lines as they are appended — the way a real observability agent (Datadog
Agent, Filebeat, etc.) would. Supported filenames: application.log, app.log,
server.log, and any *.log / *.jsonl file.

Pipeline: file change detected -> read new bytes -> parse_log_batch() ->
push structured entries into the shared mock_data `store` (so every
existing router/page keeps working unchanged) -> flag new ERROR entries so
the scheduler can trigger a LangGraph run promptly instead of waiting for
the next fixed interval.
"""
import logging
import os
import threading
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.services.log_parser import parse_log_batch

logger = logging.getLogger("guardianops.log_watcher")

WATCHED_SUFFIXES = (".log", ".jsonl")
WATCHED_NAMES = {"application.log", "app.log", "server.log"}


def _service_name_from_filename(path: Path) -> str:
    """Derive a service_id from a log filename, e.g. payment-service.log -> payment-service."""
    stem = path.stem
    for generic in ("application", "app", "server"):
        if stem == generic:
            return path.parent.name or generic
    return stem


class _LogFileState:
    """Tracks the byte offset we've already read for a single log file."""

    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        # Start at end-of-file on first sight so we only ingest *new* lines,
        # mirroring how a real tailing agent attaches to a running process.
        try:
            self.offset = path.stat().st_size
        except OSError:
            self.offset = 0


class LogWatcherService:
    def __init__(self, on_new_entries=None) -> None:
        self._states: dict[str, _LogFileState] = {}
        self._lock = threading.Lock()
        self._observer: Observer | None = None
        self.on_new_entries = on_new_entries  # callback(list[dict]) -> None
        self.new_error_count = 0

    def _is_watched(self, path: Path) -> bool:
        return path.name in WATCHED_NAMES or path.suffix in WATCHED_SUFFIXES

    def _read_new_lines(self, path: Path) -> list[str]:
        key = str(path)
        with self._lock:
            state = self._states.get(key)
            if state is None:
                state = _LogFileState(path)
                self._states[key] = state

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(state.offset)
                new_content = f.read()
                state.offset = f.tell()
        except FileNotFoundError:
            return []

        if not new_content:
            return []
        return new_content.splitlines()

    def process_file(self, path: Path) -> list[dict]:
        if not self._is_watched(path):
            return []
        lines = self._read_new_lines(path)
        if not lines:
            return []
        service_id = _service_name_from_filename(path)
        entries = parse_log_batch(lines, default_service=service_id)
        if entries:
            error_count = sum(1 for e in entries if e["level"] == "ERROR")
            self.new_error_count += error_count
            logger.info("📄 %s: ingested %d log line(s) (%d errors)", path.name, len(entries), error_count)
            if self.on_new_entries:
                try:
                    self.on_new_entries(entries)
                except Exception:  # noqa: BLE001
                    logger.exception("on_new_entries callback failed")
        return entries

    def scan_existing_files(self, logs_dir: Path) -> None:
        """On startup, register existing files (without re-ingesting old content)."""
        if not logs_dir.exists():
            return
        for root, _dirs, files in os.walk(logs_dir):
            for name in files:
                path = Path(root) / name
                if self._is_watched(path):
                    self._states[str(path)] = _LogFileState(path)

    def start(self, logs_dir: str) -> None:
        logs_path = Path(logs_dir)
        logs_path.mkdir(parents=True, exist_ok=True)
        self.scan_existing_files(logs_path)

        handler = _WatchdogHandler(self)
        self._observer = Observer()
        self._observer.schedule(handler, str(logs_path), recursive=True)
        self._observer.start()
        logger.info("👀 Log watcher started on directory: %s", logs_path.resolve())

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            logger.info("Log watcher stopped")


class _WatchdogHandler(FileSystemEventHandler):
    def __init__(self, service: LogWatcherService):
        self.service = service

    def on_modified(self, event):
        if event.is_directory:
            return
        self.service.process_file(Path(event.src_path))

    def on_created(self, event):
        if event.is_directory:
            return
        self.service.process_file(Path(event.src_path))


# Singleton instance; the callback is wired up in app/main.py at startup so
# new log entries flow straight into the shared mock_data store.
log_watcher = LogWatcherService()
