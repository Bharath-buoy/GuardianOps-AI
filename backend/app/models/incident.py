"""Pydantic models for incidents and root cause analysis."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


class TimelineEvent(BaseModel):
    timestamp: str
    label: str
    description: str
    actor: str = "GuardianOps AI"


class Incident(BaseModel):
    incident_id: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    affected_services: list[str]
    ai_summary: str
    root_cause: Optional[str] = None
    recommendation: Optional[str] = None
    confidence_score: float = 0.0
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None
    timeline: list[TimelineEvent] = []
    detected_by: str = "Incident Detection Agent"
    tags: list[str] = []


class IncidentListResponse(BaseModel):
    total: int
    open: int
    investigating: int
    resolved: int
    incidents: list[Incident]
