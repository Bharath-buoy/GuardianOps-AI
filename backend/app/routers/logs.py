"""General log query endpoint (distinct from the per-service
/infrastructure/{service_id}/logs endpoint — this one queries across all
services, real and simulated)."""
from fastapi import APIRouter, Query

from app.services.mock_data import store

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("")
async def get_logs(
    service_id: str | None = Query(default=None),
    level: str | None = Query(default=None, description="INFO | WARN | ERROR | DEBUG"),
    limit: int = Query(default=200, le=1000),
):
    logs = store.get_logs(service_id=service_id, level=level, limit=limit)
    return {"total": len(logs), "logs": logs}
