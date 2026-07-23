"""Pydantic models for infrastructure entities (services, containers, databases, APIs)."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ServiceType(str, Enum):
    API = "api"
    MICROSERVICE = "microservice"
    DATABASE = "database"
    CONTAINER = "container"
    CACHE = "cache"
    QUEUE = "queue"


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


class Service(BaseModel):
    service_id: str
    name: str
    type: ServiceType
    status: ServiceStatus
    environment: str = "production"
    region: str = "ap-south-1"
    uptime_percent: float = Field(ge=0, le=100)
    latency_ms: float
    cpu_percent: float = Field(ge=0, le=100)
    ram_percent: float = Field(ge=0, le=100)
    error_rate_percent: float = Field(ge=0, le=100)
    requests_per_min: int
    version: str = "1.0.0"
    last_deployed: str
    tags: list[str] = []
    dependencies: list[str] = []


class ServiceListResponse(BaseModel):
    total: int
    healthy: int
    degraded: int
    critical: int
    offline: int
    services: list[Service]
