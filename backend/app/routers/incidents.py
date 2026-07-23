"""Incident management endpoints."""
from fastapi import APIRouter, HTTPException, Query

from app.services.mock_data import store

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("")
async def get_incidents(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
):
    incidents = store.get_incidents(status=status, severity=severity)
    all_incidents = store.get_incidents()
    return {
        "total": len(all_incidents),
        "open": sum(1 for i in all_incidents if i["status"] == "open"),
        "investigating": sum(1 for i in all_incidents if i["status"] == "investigating"),
        "resolved": sum(1 for i in all_incidents if i["status"] == "resolved"),
        "incidents": incidents,
    }


@router.get("/{incident_id}")
async def get_incident_detail(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    recommendation = store.recommendations.get(incident_id)
    return {"incident": incident, "recommendation_detail": recommendation}
