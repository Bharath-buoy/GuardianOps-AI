"""Pydantic models for LangGraph multi-agent workflow runs."""
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class AgentStep(BaseModel):
    agent_id: str
    agent_name: str
    status: AgentStatus
    started_at: str
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    output_summary: str = ""
    details: dict[str, Any] = {}


class WorkflowRun(BaseModel):
    run_id: str
    trigger: str = "manual"
    status: AgentStatus
    started_at: str
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    steps: list[AgentStep] = []
    incidents_detected: int = 0
    recommendations_generated: int = 0
    summary: str = ""


class WorkflowRunRequest(BaseModel):
    trigger: str = "manual"
    target_service_id: Optional[str] = None
