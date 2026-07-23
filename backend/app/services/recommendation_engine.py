"""
Dynamic Recommendation Engine
================================
Generates AI recommendation text parameterized by the *actual* numbers
observed (current CPU%, error rate, offending log message, etc.) instead of
static, hardcoded sentences. Each `build_*` function takes real
measurements and composes a recommendation whose wording changes with the
severity and specifics of the underlying signal — e.g. the suggested
replica/pool-size scale factor grows with how far over threshold the metric
is.

This is still a deterministic rule engine (no external LLM call required,
matching the rest of GuardianOps AI's zero-API-key design), but the output
is computed, not templated with fixed filler text.
"""
import math


def _severity_from_ratio(ratio: float) -> str:
    """ratio = observed / threshold. >2x -> critical, >1.4x -> high, else medium."""
    if ratio >= 2.0:
        return "critical"
    if ratio >= 1.4:
        return "high"
    return "medium"


def _scale_suggestion(ratio: float) -> int:
    """Suggests how many extra replicas/pool slots to add, scaling with severity."""
    return max(1, min(6, math.ceil((ratio - 1) * 4)))


def build_cpu_recommendation(service_id: str, cpu_percent: float, threshold: float = 75.0) -> dict:
    ratio = cpu_percent / threshold
    extra = _scale_suggestion(ratio)
    severity = _severity_from_ratio(ratio)
    return {
        "title": f"High CPU usage on {service_id}",
        "summary": f"CPU utilization on {service_id} measured at {cpu_percent:.1f}%, "
        f"{cpu_percent - threshold:.1f} points above the {threshold:.0f}% threshold.",
        "root_cause": f"Sustained CPU load of {cpu_percent:.1f}% suggests either a compute-bound "
        f"hotspot in {service_id} or insufficient horizontal capacity for current traffic.",
        "recommendation": f"Scale {service_id} by {extra} additional replica(s) and profile the "
        f"highest CPU-consuming request path to rule out an inefficient loop or algorithm.",
        "severity": severity,
        "confidence": round(min(0.97, 0.7 + ratio * 0.1), 2),
    }


def build_ram_recommendation(service_id: str, ram_percent: float, threshold: float = 80.0) -> dict:
    ratio = ram_percent / threshold
    severity = _severity_from_ratio(ratio)
    return {
        "title": f"High memory usage on {service_id}",
        "summary": f"RAM utilization on {service_id} reached {ram_percent:.1f}%, "
        f"{ram_percent - threshold:.1f} points above the {threshold:.0f}% threshold.",
        "root_cause": f"Memory pressure at {ram_percent:.1f}% may indicate an unbounded cache, "
        f"object retention, or a memory leak building up in {service_id}.",
        "recommendation": f"Set an explicit memory limit and eviction policy on {service_id}, "
        f"capture a heap snapshot if usage continues climbing, and restart the process as a "
        f"short-term mitigation if it approaches {min(99, threshold + 15):.0f}%.",
        "severity": severity,
        "confidence": round(min(0.96, 0.68 + ratio * 0.1), 2),
    }


def build_disk_recommendation(service_id: str, disk_percent: float, threshold: float = 85.0) -> dict:
    ratio = disk_percent / threshold
    severity = _severity_from_ratio(ratio)
    remaining_estimate = max(0, 100 - disk_percent)
    return {
        "title": f"High disk usage on {service_id}",
        "summary": f"Disk utilization at {disk_percent:.1f}% with approximately {remaining_estimate:.1f}% "
        f"free space remaining.",
        "root_cause": "Log rotation may be misconfigured, or a data/temp directory is growing "
        "unbounded without cleanup.",
        "recommendation": f"Enable/verify log rotation, purge temp files older than 7 days, and "
        f"provision additional disk capacity before free space drops below "
        f"{max(5, int(remaining_estimate / 2))}%.",
        "severity": severity,
        "confidence": round(min(0.95, 0.65 + ratio * 0.1), 2),
    }


def build_network_recommendation(service_id: str, throughput_kbps: float, threshold: float = 5000.0) -> dict:
    ratio = throughput_kbps / threshold
    severity = _severity_from_ratio(ratio)
    return {
        "title": f"Elevated network throughput on {service_id}",
        "summary": f"Combined network throughput measured at {throughput_kbps:.0f} KB/s, "
        f"{ratio:.1f}x the baseline of {threshold:.0f} KB/s.",
        "root_cause": "A traffic spike, retry storm, or an unusually large payload/response size "
        "is driving throughput above baseline.",
        "recommendation": "Inspect recent deploys for oversized payloads, confirm no retry loop "
        "is amplifying request volume, and consider rate limiting if the spike is unexpected.",
        "severity": severity,
        "confidence": round(min(0.9, 0.6 + ratio * 0.08), 2),
    }


def build_response_time_recommendation(service_id: str, latency_ms: float, threshold: float = 300.0) -> dict:
    ratio = latency_ms / threshold
    extra = _scale_suggestion(ratio)
    severity = _severity_from_ratio(ratio)
    return {
        "title": f"High response time on {service_id}",
        "summary": f"p95 latency on {service_id} measured at {latency_ms:.0f}ms against a "
        f"{threshold:.0f}ms SLO — {(ratio - 1) * 100:.0f}% over budget.",
        "root_cause": f"Latency this far above baseline typically points to a slow downstream "
        f"dependency, lock contention, or connection pool exhaustion in {service_id}.",
        "recommendation": f"Add request-level tracing to isolate the slow span, and increase "
        f"{service_id}'s connection pool / add {extra} replica(s) to absorb the load.",
        "severity": severity,
        "confidence": round(min(0.94, 0.7 + ratio * 0.08), 2),
    }


def build_log_pattern_recommendation(service_id: str, pattern: str, occurrences: int, sample_message: str) -> dict:
    """Builds a recommendation for a log-derived issue: db timeout, connection
    failure, frequent exceptions, or memory-leak indicators."""
    severity = "critical" if occurrences >= 8 else "high" if occurrences >= 4 else "medium"

    catalog = {
        "database_timeout": {
            "title": f"Database timeout detected on {service_id}",
            "root_cause": f"{occurrences} database timeout event(s) observed in recent logs for "
            f"{service_id}, indicating the DB is not responding within the configured timeout window.",
            "recommendation": "Check database connection pool saturation and long-running queries; "
            "consider increasing statement_timeout headroom or adding a read replica.",
        },
        "connection_failure": {
            "title": f"Connection failures on {service_id}",
            "root_cause": f"{occurrences} connection failure event(s) logged for {service_id}, "
            f"suggesting a downstream dependency is unreachable or refusing connections.",
            "recommendation": "Verify the downstream service's health/DNS resolution and add a "
            "circuit breaker with exponential backoff around the failing client call.",
        },
        "frequent_exceptions": {
            "title": f"Frequent exceptions in {service_id}",
            "root_cause": f"{occurrences} exception(s) logged for {service_id} in the recent window, "
            f"well above the expected baseline — most recently: \"{sample_message[:120]}\".",
            "recommendation": "Triage the most frequent stack trace first; add a regression test "
            "covering the failing code path before the next deploy.",
        },
        "memory_leak_indicator": {
            "title": f"Possible memory leak in {service_id}",
            "root_cause": f"Log pattern in {service_id} ({occurrences} occurrence(s)) is consistent "
            f"with gradually accumulating memory that is never released.",
            "recommendation": "Capture heap snapshots over a fixed interval to confirm growth, and "
            "audit recently added caches/listeners for missing cleanup/unsubscribe logic.",
        },
    }
    entry = catalog.get(
        pattern,
        {
            "title": f"Anomalous log pattern on {service_id}",
            "root_cause": f"Detected {occurrences} occurrence(s) of an unusual log pattern.",
            "recommendation": "Review recent log activity for this service.",
        },
    )
    return {
        **entry,
        "summary": entry["root_cause"],
        "severity": severity,
        "confidence": round(min(0.93, 0.6 + occurrences * 0.04), 2),
    }
