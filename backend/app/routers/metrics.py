"""Real system metrics endpoints (psutil-backed)."""
from fastapi import APIRouter

from app.services.mock_data import store
from app.services.system_monitor import get_system_snapshot

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("")
async def get_metrics():
    """Returns a fresh real-time system metrics snapshot (CPU, RAM, disk,
    network, processes, uptime) collected directly via psutil."""
    return get_system_snapshot()


@router.get("/history")
async def get_metrics_history(limit: int = 100):
    """Returns recent historical system metric snapshots collected by the
    scheduler/Infrastructure Health Agent on each workflow run."""
    history = store.system_metrics_history[-limit:]
    return {"total": len(store.system_metrics_history), "snapshots": history}


@router.get("/services/{service_id}")
async def get_service_metrics_history(service_id: str, limit: int = 200):
    """Returns time-series metrics for a single service (real or simulated)."""
    points = store.get_metrics(service_id).get(service_id, [])
    return {"service_id": service_id, "points": points[-limit:]}
