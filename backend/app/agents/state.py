"""Shared state schema passed between LangGraph agent nodes."""
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    run_id: str
    trigger: str
    target_service_id: str | None

    # Populated progressively by each agent node
    services_snapshot: list[dict]
    infra_health_report: dict
    log_findings: dict
    metrics_findings: dict
    api_findings: dict
    detected_incidents: list[dict]
    root_cause_reports: dict[str, str]
    recommendations: dict[str, str]
    notifications_sent: list[dict]

    steps: list[dict]
    incidents_created: list[dict]


# Ordered list of (agent_id, agent_name) pairs used both by the LangGraph builder
# (app/agents/graph.py) and by mock workflow-history generation
# (app/services/mock_data.py). Lives here — rather than in graph.py — because
# graph.py imports nodes.py which imports the mock data store, and the mock
# data store needs this sequence during its own bootstrap. Keeping it in this
# dependency-free module avoids a circular import between mock_data <-> graph.
AGENT_SEQUENCE = [
    ("infra-health", "Infrastructure Health Agent"),
    ("log-analysis", "Log Analysis Agent"),
    ("metrics", "Metrics Agent"),
    ("api-monitoring", "API Monitoring Agent"),
    ("incident-detection", "Incident Detection Agent"),
    ("root-cause-analysis", "Root Cause Analysis Agent"),
    ("recommendation", "Recommendation Agent"),
    ("notification", "Notification Agent"),
]
