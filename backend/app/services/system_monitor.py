"""
Real System Monitoring Service
================================
Collects genuine host-level metrics using `psutil` — CPU, RAM, disk,
network, running processes, and system uptime. This is the "real AIOps"
counterpart to the simulated telemetry in `mock_data.py`; the LangGraph
agents consult this module (via `get_system_snapshot`) when
`settings.LIVE_MONITORING` is enabled.
"""
import logging
import time
from datetime import datetime, timezone

import psutil

logger = logging.getLogger("guardianops.system_monitor")

_boot_time = psutil.boot_time()
_last_net_io = psutil.net_io_counters()
_last_net_time = time.time()


def get_cpu_usage() -> dict:
    """CPU utilization — overall percent + per-core breakdown + load context."""
    per_core = psutil.cpu_percent(percpu=True, interval=None)
    freq = None
    try:
        freq_info = psutil.cpu_freq()
        freq = round(freq_info.current, 1) if freq_info else None
    except Exception:  # noqa: BLE001 — cpu_freq unsupported on some platforms/containers
        freq = None
    return {
        "percent": psutil.cpu_percent(interval=None),
        "per_core_percent": per_core,
        "core_count_logical": psutil.cpu_count(logical=True),
        "core_count_physical": psutil.cpu_count(logical=False),
        "frequency_mhz": freq,
    }


def get_ram_usage() -> dict:
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "percent": mem.percent,
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "swap_percent": swap.percent,
    }


def get_disk_usage() -> dict:
    usage = psutil.disk_usage("/")
    io_counters = None
    try:
        io = psutil.disk_io_counters()
        if io:
            io_counters = {
                "read_mb": round(io.read_bytes / (1024 ** 2), 1),
                "write_mb": round(io.write_bytes / (1024 ** 2), 1),
            }
    except Exception:  # noqa: BLE001
        io_counters = None
    return {
        "percent": usage.percent,
        "total_gb": round(usage.total / (1024 ** 3), 2),
        "used_gb": round(usage.used / (1024 ** 3), 2),
        "free_gb": round(usage.free / (1024 ** 3), 2),
        "io_counters": io_counters,
    }


def get_network_usage() -> dict:
    """Computes throughput (KB/s) since the last call using a module-level snapshot."""
    global _last_net_io, _last_net_time
    current = psutil.net_io_counters()
    now = time.time()
    elapsed = max(0.5, now - _last_net_time)

    sent_rate_kbps = round(max(0, current.bytes_sent - _last_net_io.bytes_sent) / 1024 / elapsed, 2)
    recv_rate_kbps = round(max(0, current.bytes_recv - _last_net_io.bytes_recv) / 1024 / elapsed, 2)

    _last_net_io = current
    _last_net_time = now

    return {
        "bytes_sent_total": current.bytes_sent,
        "bytes_recv_total": current.bytes_recv,
        "sent_kbps": sent_rate_kbps,
        "recv_kbps": recv_rate_kbps,
        "packets_sent": current.packets_sent,
        "packets_recv": current.packets_recv,
        "errin": current.errin,
        "errout": current.errout,
    }


def get_running_processes(limit: int = 10) -> list[dict]:
    """Top processes by CPU usage."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            info = p.info
            procs.append(
                {
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu_percent": round(info["cpu_percent"] or 0.0, 1),
                    "memory_percent": round(info["memory_percent"] or 0.0, 2),
                    "status": info["status"],
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda p: p["cpu_percent"], reverse=True)
    return procs[:limit]


def get_system_uptime() -> dict:
    uptime_seconds = int(time.time() - _boot_time)
    days, rem = divmod(uptime_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    return {
        "boot_time": datetime.fromtimestamp(_boot_time, tz=timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{days}d {hours}h {minutes}m",
    }


def get_system_snapshot() -> dict:
    """Full real-time system metrics snapshot — the primary export used by
    the scheduler and the LangGraph Metrics Agent."""
    try:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": get_cpu_usage(),
            "ram": get_ram_usage(),
            "disk": get_disk_usage(),
            "network": get_network_usage(),
            "uptime": get_system_uptime(),
            "top_processes": get_running_processes(limit=10),
            "process_count": len(psutil.pids()),
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to collect system snapshot: %s", exc)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }
