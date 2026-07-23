"""Pydantic models for standalone Guardian Agent telemetry (see /guardian-agent)."""
from typing import Optional

from pydantic import BaseModel, Field


class GuardianAgentMetrics(BaseModel):
    """Mirrors the shape produced by backend/app/services/system_monitor.py's
    get_system_snapshot(), so the same real-metrics pipeline (apply_system_metrics
    -> Infrastructure Health Agent -> incident_rules) works unmodified whether the
    snapshot came from the local backend host or a remote Guardian Agent."""

    timestamp: str
    cpu: dict
    ram: dict
    disk: dict
    network: dict
    uptime: dict
    process_count: int
    top_processes: list[dict] = []


class GuardianAgentLogLine(BaseModel):
    service_id: str = Field(description="Logical service/app name this line belongs to, e.g. the log filename stem")
    line: str = Field(description="Raw log line text — parsed server-side by app/services/log_parser.py")


class GuardianAgentTelemetryIn(BaseModel):
    agent_id: str
    hostname: str
    os: str
    metrics: Optional[GuardianAgentMetrics] = None
    logs: list[GuardianAgentLogLine] = []


class GuardianAgentPublic(BaseModel):
    agent_id: str
    hostname: str
    os: str
    service_id: str
    first_seen: str
    last_seen: str
    online: bool


class GuardianAgentTelemetryAck(BaseModel):
    accepted: bool
    agent_id: str
    metrics_ingested: bool
    logs_ingested: int
    server_time: str
