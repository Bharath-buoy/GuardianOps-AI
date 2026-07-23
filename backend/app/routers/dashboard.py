"""Dashboard aggregation endpoint."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.services.mock_data import store

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard():
    services = store.get_services()
    counts = store.summary_counts()
    incidents = store.get_incidents()
    recent_incidents = incidents[:5]
    open_incidents = [i for i in incidents if i["status"] != "resolved"]

    avg_latency = round(sum(s["latency_ms"] for s in services) / max(1, len(services)), 1)
    avg_cpu = round(sum(s["cpu_percent"] for s in services) / max(1, len(services)), 1)
    avg_ram = round(sum(s["ram_percent"] for s in services) / max(1, len(services)), 1)
    avg_error_rate = round(sum(s["error_rate_percent"] for s in services) / max(1, len(services)), 2)

    health_score = round(100 * (counts["healthy"] + 0.5 * counts["degraded"]) / max(1, counts["total"]), 1)

    workflow_runs = store.get_workflow_runs(limit=1)
    last_run = workflow_runs[0] if workflow_runs else None

    recent_activities = []
    for incident in incidents[:8]:
        recent_activities.append(
            {
                "type": "incident",
                "message": incident["title"],
                "severity": incident["severity"],
                "timestamp": incident["created_at"],
            }
        )
    for run in store.get_workflow_runs(limit=3):
        recent_activities.append(
            {
                "type": "workflow",
                "message": f"Workflow {run['run_id']} completed ({run['incidents_detected']} incidents found)",
                "severity": "info",
                "timestamp": run["started_at"],
            }
        )
    recent_activities.sort(key=lambda a: a["timestamp"], reverse=True)

    return {
        "health_score": health_score,
        "service_counts": counts,
        "kpis": {
            "avg_response_time_ms": avg_latency,
            "avg_cpu_percent": avg_cpu,
            "avg_ram_percent": avg_ram,
            "avg_error_rate_percent": avg_error_rate,
        },
        "recent_incidents": recent_incidents,
        "open_incidents_count": len(open_incidents),
        "ai_workflow_status": {
            "last_run_id": last_run["run_id"] if last_run else None,
            "last_run_status": last_run["status"] if last_run else "idle",
            "last_run_at": last_run["started_at"] if last_run else None,
            "total_runs": len(store.workflow_runs),
        },
        "recent_activities": recent_activities[:10],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
