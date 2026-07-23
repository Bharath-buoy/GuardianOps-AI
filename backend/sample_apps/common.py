"""
Shared helper for GuardianOps AI sample applications.

Each sample app is a tiny standalone script that behaves like a real
production service: it continuously appends realistic log lines (in the
exact text format GuardianOps AI's log_parser understands) to its own log
file under LOGS_DIR. GuardianOps AI's watchdog-based log watcher tails
these files in real time — no manual upload, no mocking.

Log line format (matches app/services/log_parser.py's TEXT_LOG_PATTERN):
    2026-07-22 10:15:32 [ERROR] payment-service: Database connection timeout
"""
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOGS_DIR = os.environ.get("GUARDIANOPS_LOGS_DIR", "./sample_apps/logs")


def get_log_path(service_name: str, logs_dir: str = DEFAULT_LOGS_DIR) -> Path:
    logs_path = Path(logs_dir)
    logs_path.mkdir(parents=True, exist_ok=True)
    return logs_path / f"{service_name}.log"


def write_log(service_name: str, level: str, message: str, logs_dir: str = DEFAULT_LOGS_DIR) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} [{level}] {service_name}: {message}\n"
    path = get_log_path(service_name, logs_dir)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def write_stack_trace(service_name: str, exception_line: str, logs_dir: str = DEFAULT_LOGS_DIR) -> None:
    """Appends a fake (but plausible-looking) stack trace immediately after
    an ERROR line, matching the multi-line format the log parser attaches
    to the preceding error entry."""
    path = get_log_path(service_name, logs_dir)
    trace_lines = [
        "Traceback (most recent call last):",
        f'  File "{service_name}/handler.py", line {random.randint(20, 220)}, in handle_request',
        f"    result = process(payload)",
        f'  File "{service_name}/core.py", line {random.randint(10, 150)}, in process',
        f"    {exception_line}",
    ]
    with open(path, "a", encoding="utf-8") as f:
        for line in trace_lines:
            f.write(line + "\n")


def run_service_loop(service_name: str, scenario_fn, min_interval: float = 1.5, max_interval: float = 4.0) -> None:
    """Generic driver loop: repeatedly calls scenario_fn(service_name) with
    randomized pacing so multiple sample apps don't write in lockstep."""
    print(f"[{service_name}] sample application started — writing logs to {get_log_path(service_name)}")
    try:
        while True:
            scenario_fn(service_name)
            time.sleep(random.uniform(min_interval, max_interval))
    except KeyboardInterrupt:
        print(f"[{service_name}] stopped")
