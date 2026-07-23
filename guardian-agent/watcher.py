"""
Guardian Agent - Log Watcher
==============================
Watches a directory for application log files and tails new lines as they're
appended, using `watchdog`. Kept deliberately dumb: this module only detects
and buffers *raw* new lines — GuardianOps AI's backend does all structured
parsing (timestamp/service/severity/stack-trace extraction) server-side via
the same log_parser.py it already uses for locally-watched logs. This keeps
the agent lightweight and means log-format improvements only ever need to
ship on the server, not to every installed agent.

Supported filenames: application.log, app.log, server.log, and any
*.log / *.jsonl file.
"""
import os
import threading
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WATCHED_SUFFIXES = (".log", ".jsonl")
WATCHED_NAMES = {"application.log", "app.log", "server.log"}


def service_name_from_filename(path: Path) -> str:
    """Derive a service_id from a log filename, e.g. payment-service.log ->
    payment-service. Generic names (application.log/app.log/server.log) fall
    back to the parent folder name, matching the backend's own convention
    (see backend/app/services/log_watcher.py) so agent-sourced and
    locally-watched logs behave identically."""
    stem = path.stem
    for generic in ("application", "app", "server"):
        if stem == generic:
            return path.parent.name or generic
    return stem


class _FileState:
    """Tracks the byte offset already read for a single log file."""

    def __init__(self, path: Path):
        self.path = path
        try:
            # Start at end-of-file on first sight so only *new* lines are
            # ever sent — never re-uploads a file's pre-existing history.
            self.offset = path.stat().st_size
        except OSError:
            self.offset = 0


class LogWatcher:
    def __init__(self) -> None:
        self._states: dict[str, _FileState] = {}
        self._lock = threading.Lock()
        self._observer: Observer | None = None
        # buffer: list of {"service_id": ..., "line": ...} ready to be sent
        self._buffer: list[dict] = []

    def _is_watched(self, path: Path) -> bool:
        return path.name in WATCHED_NAMES or path.suffix in WATCHED_SUFFIXES

    def _read_new_lines(self, path: Path) -> list[str]:
        key = str(path)
        with self._lock:
            state = self._states.get(key)
            if state is None:
                state = _FileState(path)
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
        return [line for line in new_content.splitlines() if line.strip()]

    def _on_file_event(self, path: Path) -> None:
        if not self._is_watched(path):
            return
        lines = self._read_new_lines(path)
        if not lines:
            return
        service_id = service_name_from_filename(path)
        with self._lock:
            for line in lines:
                self._buffer.append({"service_id": service_id, "line": line})

    def drain(self) -> list[dict]:
        """Returns and clears everything buffered since the last drain —
        called once per send cycle by agent.py."""
        with self._lock:
            batch, self._buffer = self._buffer, []
        return batch

    def scan_existing_files(self, logs_dir: Path) -> None:
        """On startup, register existing files at their current size so we
        never re-upload old/pre-existing log content."""
        if not logs_dir.exists():
            return
        for root, _dirs, files in os.walk(logs_dir):
            for name in files:
                path = Path(root) / name
                if self._is_watched(path):
                    self._states[str(path)] = _FileState(path)

    def start(self, logs_dir: str) -> None:
        logs_path = Path(logs_dir)
        logs_path.mkdir(parents=True, exist_ok=True)
        self.scan_existing_files(logs_path)

        handler = _Handler(self)
        self._observer = Observer()
        self._observer.schedule(handler, str(logs_path), recursive=True)
        self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)


class _Handler(FileSystemEventHandler):
    def __init__(self, watcher: LogWatcher):
        self.watcher = watcher

    def on_modified(self, event):
        if not event.is_directory:
            self.watcher._on_file_event(Path(event.src_path))  # noqa: SLF001

    def on_created(self, event):
        if not event.is_directory:
            self.watcher._on_file_event(Path(event.src_path))  # noqa: SLF001