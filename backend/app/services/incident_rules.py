"""
Real-Data Incident Detection Rules
=====================================
Threshold- and pattern-based detectors that turn real psutil metrics and
real parsed application logs into incidents, using the dynamic
recommendation_engine (rather than fixed hardcoded text) for the
resulting summary/root-cause/recommendation.

Covers the incident types required by the AIOps spec:
  - High CPU / RAM / Disk / Network usage
  - High response time
  - Database timeout
  - Connection failure
  - Frequent exceptions
  - Memory leak indicators
"""
import re

from app.services import recommendation_engine as rec

CPU_THRESHOLD = 75.0
RAM_THRESHOLD = 80.0
DISK_THRESHOLD = 85.0
NETWORK_THRESHOLD_KBPS = 5000.0
LATENCY_THRESHOLD_MS = 300.0

LOG_PATTERNS = {
    "database_timeout": re.compile(r"database.{0,20}(timeout|timed out)|query.{0,20}timeout", re.I),
    "connection_failure": re.compile(r"connection (refused|failed|reset)|failed to (connect|reach)", re.I),
    "memory_leak_indicator": re.compile(r"(memory leak|out of memory|OOM|heap.{0,15}(exhausted|full))", re.I),
}


def detect_metric_incidents(service: dict) -> list[dict]:
    """Checks a single service's current metrics against fixed thresholds."""
    incidents: list[dict] = []
    service_id = service["service_id"]

    if service.get("cpu_percent", 0) > CPU_THRESHOLD:
        incidents.append(rec.build_cpu_recommendation(service_id, service["cpu_percent"], CPU_THRESHOLD))
    if service.get("ram_percent", 0) > RAM_THRESHOLD:
        incidents.append(rec.build_ram_recommendation(service_id, service["ram_percent"], RAM_THRESHOLD))
    if service.get("disk_percent") and service["disk_percent"] > DISK_THRESHOLD:
        incidents.append(rec.build_disk_recommendation(service_id, service["disk_percent"], DISK_THRESHOLD))
    if service.get("latency_ms", 0) > LATENCY_THRESHOLD_MS and service.get("type") != "container":
        incidents.append(rec.build_response_time_recommendation(service_id, service["latency_ms"], LATENCY_THRESHOLD_MS))

    return incidents


def detect_network_incident(service_id: str, throughput_kbps: float) -> dict | None:
    if throughput_kbps > NETWORK_THRESHOLD_KBPS:
        return rec.build_network_recommendation(service_id, throughput_kbps, NETWORK_THRESHOLD_KBPS)
    return None


def detect_log_incidents(service_id: str, recent_logs: list[dict]) -> list[dict]:
    """Scans a service's recent real log lines for known problem patterns."""
    incidents: list[dict] = []
    error_logs = [l for l in recent_logs if l["level"] == "ERROR"]

    # Frequent exceptions: simple volume-based check
    if len(error_logs) >= 4:
        incidents.append(
            rec.build_log_pattern_recommendation(
                service_id,
                "frequent_exceptions",
                len(error_logs),
                error_logs[0]["message"] if error_logs else "",
            )
        )

    # Pattern-based checks (db timeout, connection failure, memory leak hints)
    for pattern_name, regex in LOG_PATTERNS.items():
        matches = [l for l in recent_logs if regex.search(l.get("message", ""))]
        if matches:
            incidents.append(
                rec.build_log_pattern_recommendation(
                    service_id, pattern_name, len(matches), matches[0]["message"]
                )
            )

    return incidents
