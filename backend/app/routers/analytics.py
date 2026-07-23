"""Analytics endpoint - aggregated trends for charts."""
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.services.mock_data import store

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("")
async def get_analytics():
    services = store.get_services()
    all_metrics = store.get_metrics()

    # Build a time-bucketed series (hourly averages) across all services
    buckets: dict[str, dict] = {}
    for service_id, points in all_metrics.items():
        for p in points:
            hour_key = p["timestamp"][:13]  # YYYY-MM-DDTHH
            b = buckets.setdefault(
                hour_key, {"cpu": [], "ram": [], "latency": [], "error_rate": []}
            )
            b["cpu"].append(p["cpu_percent"])
            b["ram"].append(p["ram_percent"])
            b["latency"].append(p["latency_ms"])
            b["error_rate"].append(p["error_rate_percent"])

    response_time_trend = []
    cpu_trend = []
    ram_trend = []
    error_trend = []
    for hour_key in sorted(buckets.keys()):
        b = buckets[hour_key]
        response_time_trend.append({"time": hour_key, "value": round(sum(b["latency"]) / len(b["latency"]), 1)})
        cpu_trend.append({"time": hour_key, "value": round(sum(b["cpu"]) / len(b["cpu"]), 1)})
        ram_trend.append({"time": hour_key, "value": round(sum(b["ram"]) / len(b["ram"]), 1)})
        error_trend.append({"time": hour_key, "value": round(sum(b["error_rate"]) / len(b["error_rate"]), 2)})

    incidents = store.get_incidents()
    severity_counts = Counter(i["severity"] for i in incidents)
    incident_trend_by_day: dict[str, int] = {}
    for i in incidents:
        day_key = i["created_at"][:10]
        incident_trend_by_day[day_key] = incident_trend_by_day.get(day_key, 0) + 1
    incident_trend = [
        {"date": d, "count": c} for d, c in sorted(incident_trend_by_day.items())
    ]

    top_failing = sorted(
        services,
        key=lambda s: (s["error_rate_percent"], -s["uptime_percent"]),
        reverse=True,
    )[:5]

    availability = [
        {"service_id": s["service_id"], "uptime_percent": s["uptime_percent"]}
        for s in sorted(services, key=lambda s: s["uptime_percent"])[:8]
    ]

    return {
        "response_time_trend": response_time_trend[-48:],
        "cpu_trend": cpu_trend[-48:],
        "ram_trend": ram_trend[-48:],
        "error_rate_trend": error_trend[-48:],
        "incident_trend": incident_trend[-14:],
        "severity_breakdown": dict(severity_counts),
        "top_failing_services": [
            {
                "service_id": s["service_id"],
                "error_rate_percent": s["error_rate_percent"],
                "uptime_percent": s["uptime_percent"],
                "latency_ms": s["latency_ms"],
            }
            for s in top_failing
        ],
        "service_availability": availability,
    }
