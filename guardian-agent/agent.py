#!/usr/bin/env python3
"""
GuardianOps AI - Guardian Agent
==================================
A lightweight, standalone telemetry agent. Install it on any machine you want
GuardianOps AI to monitor: it collects real system metrics (via psutil) and
tails application log files (via watchdog), then POSTs a telemetry batch to
your GuardianOps AI backend every `send_interval_seconds` (default: 30s).

Run:
    python agent.py                    # uses config.json in this folder
    python agent.py --config my.json   # uses a different config file

See README.md for full installation and connection instructions.
"""
import argparse
import json
import logging
import platform
import socket
import sys
import time
import uuid
from pathlib import Path

import requests

from collector import get_system_snapshot
from watcher import LogWatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | guardian-agent | %(message)s",
)
logger = logging.getLogger("guardian-agent")


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        logger.error("Config file not found: %s", config_path)
        logger.error("Copy config.json and edit server_url / api_key before running.")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Auto-generate and persist a stable agent_id on first run, so restarts
    # keep the same identity in GuardianOps AI's agent registry instead of
    # registering as a "new" agent every time the process restarts.
    if not config.get("agent_id"):
        config["agent_id"] = f"guardian-{uuid.uuid4().hex[:12]}"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logger.info("Generated new agent_id: %s (saved to %s)", config["agent_id"], config_path)

    required = ["server_url", "api_key"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        logger.error("Missing required config field(s): %s", ", ".join(missing))
        sys.exit(1)
    if config["api_key"] == "change-this-to-a-long-random-string":
        logger.warning(
            "⚠️  api_key is still the default placeholder — set it to match "
            "AGENT_API_KEY on your GuardianOps AI backend before deploying."
        )

    config.setdefault("logs_dir", "./logs")
    config.setdefault("send_interval_seconds", 30)
    config.setdefault("request_timeout_seconds", 10)
    return config


def send_telemetry(config: dict, hostname: str, os_name: str, log_watcher: LogWatcher) -> bool:
    metrics = get_system_snapshot()
    logs = log_watcher.drain()

    payload = {
        "agent_id": config["agent_id"],
        "hostname": hostname,
        "os": os_name,
        "metrics": None if "error" in metrics else metrics,
        "logs": logs,
    }

    url = config["server_url"].rstrip("/") + "/api/agents/telemetry"
    headers = {
        "Content-Type": "application/json",
        "X-Agent-Api-Key": config["api_key"],
    }

    try:
        resp = requests.post(
            url, json=payload, headers=headers, timeout=config["request_timeout_seconds"]
        )
    except requests.exceptions.RequestException as exc:
        logger.warning("Failed to reach GuardianOps AI at %s: %s", url, exc)
        return False

    if resp.status_code == 200:
        ack = resp.json()
        logger.info(
            "✅ Telemetry sent — metrics_ingested=%s, logs_ingested=%s",
            ack.get("metrics_ingested"),
            ack.get("logs_ingested"),
        )
        return True

    if resp.status_code == 401:
        logger.error("❌ Rejected (401): API key doesn't match the backend's AGENT_API_KEY.")
    elif resp.status_code == 503:
        logger.error("❌ Rejected (503): Agent telemetry ingestion is disabled on the backend "
                     "(AGENT_API_KEY not configured there).")
    else:
        logger.error("❌ Unexpected response %s: %s", resp.status_code, resp.text[:200])
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="GuardianOps AI Guardian Agent")
    parser.add_argument(
        "--config", default="config.json", help="Path to config.json (default: ./config.json)"
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)

    hostname = socket.gethostname()
    os_name = f"{platform.system()}-{platform.release()}"

    logger.info("🛡️  GuardianOps AI Guardian Agent starting")
    logger.info("    agent_id : %s", config["agent_id"])
    logger.info("    hostname : %s", hostname)
    logger.info("    os       : %s", os_name)
    logger.info("    server   : %s", config["server_url"])
    logger.info("    logs_dir : %s", config["logs_dir"])
    logger.info("    interval : %ss", config["send_interval_seconds"])

    log_watcher = LogWatcher()
    log_watcher.start(config["logs_dir"])
    logger.info("👀 Watching %s for application.log / app.log / server.log / *.log / *.jsonl", config["logs_dir"])

    try:
        while True:
            send_telemetry(config, hostname, os_name, log_watcher)
            time.sleep(config["send_interval_seconds"])
    except KeyboardInterrupt:
        logger.info("Shutting down (Ctrl+C received)...")
    finally:
        log_watcher.stop()
        logger.info("👋 Guardian Agent stopped")


if __name__ == "__main__":
    main()
