"""On-demand analysis endpoint - runs a lightweight subset of agent logic
against a single service without triggering the full workflow."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.mock_data import store

router = APIRouter(prefix="/analyze", tags=["Analyze"])


class AnalyzeRequest(BaseModel):
    service_id: str


@router.post("")
async def analyze_service(payload: AnalyzeRequest):
    service = store.get_service(payload.service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{payload.service_id}' not found")

    issues = []
    if service["cpu_percent"] > 75:
        issues.append("High CPU utilization detected")
    if service["ram_percent"] > 80:
        issues.append("High memory utilization detected")
    if service["error_rate_percent"] > 2:
        issues.append("Elevated error rate above SLO threshold")
    if service["latency_ms"] > 300:
        issues.append("Latency above acceptable threshold")

    risk_level = "critical" if len(issues) >= 3 else "medium" if issues else "low"

    return {
        "service_id": service["service_id"],
        "status": service["status"],
        "risk_level": risk_level,
        "issues_found": issues,
        "recommendation": (
            "Scale resources and review recent deployments."
            if issues
            else "No immediate action required — service operating within healthy thresholds."
        ),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
