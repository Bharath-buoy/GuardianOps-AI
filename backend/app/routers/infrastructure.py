"""Infrastructure inventory endpoint - services, containers, DBs, APIs."""
from fastapi import APIRouter, HTTPException, Query

from app.services.mock_data import store

router = APIRouter(prefix="/infrastructure", tags=["Infrastructure"])


@router.get("")
async def get_infrastructure(
    type: str | None = Query(default=None, description="Filter by service type"),
    status: str | None = Query(default=None, description="Filter by status"),
):
    services = store.get_services()
    if type:
        services = [s for s in services if s["type"] == type]
    if status:
        services = [s for s in services if s["status"] == status]

    counts = store.summary_counts()
    return {
        "total": counts["total"],
        "healthy": counts["healthy"],
        "degraded": counts["degraded"],
        "critical": counts["critical"],
        "offline": counts["offline"],
        "services": services,
    }


@router.get("/{service_id}")
async def get_service_detail(service_id: str):
    service = store.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    metrics = store.get_metrics(service_id).get(service_id, [])
    logs = store.get_logs(service_id=service_id, limit=50)
    return {"service": service, "metrics_history": metrics, "recent_logs": logs}


@router.get("/{service_id}/logs")
async def get_service_logs(service_id: str, level: str | None = None, limit: int = 100):
    if not store.get_service(service_id):
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    return {"service_id": service_id, "logs": store.get_logs(service_id=service_id, level=level, limit=limit)}
