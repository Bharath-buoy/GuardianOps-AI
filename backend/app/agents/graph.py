"""
GuardianOps AI - LangGraph Multi-Agent Orchestration
=====================================================
Wires the 8 specialized agents into a single directed workflow using
LangGraph's StateGraph. The pipeline mirrors a real observability
platform's reasoning chain:

  Infrastructure Health -> Log Analysis -> Metrics -> API Monitoring
        -> Incident Detection -> Root Cause Analysis -> Recommendation
        -> Notification -> (MongoDB persistence + Dashboard update)

The graph is compiled once at import time and reused across requests.
"""
import uuid
from datetime import datetime, timezone

from langgraph.graph import END, StateGraph

from app.agents.nodes import (
    api_monitoring_agent,
    incident_detection_agent,
    infrastructure_health_agent,
    log_analysis_agent,
    metrics_agent,
    notification_agent,
    recommendation_agent,
    root_cause_analysis_agent,
)
from app.agents.state import AGENT_SEQUENCE, AgentState

# AGENT_SEQUENCE (ordered list of (agent_id, agent_name) pairs) is defined in
# state.py and re-exported here for backwards-compatible imports elsewhere
# (e.g. `from app.agents.graph import AGENT_SEQUENCE`).


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("infra_health", infrastructure_health_agent)
    graph.add_node("log_analysis", log_analysis_agent)
    graph.add_node("metrics", metrics_agent)
    graph.add_node("api_monitoring", api_monitoring_agent)
    graph.add_node("incident_detection", incident_detection_agent)
    graph.add_node("root_cause_analysis", root_cause_analysis_agent)
    graph.add_node("recommendation", recommendation_agent)
    graph.add_node("notification", notification_agent)

    graph.set_entry_point("infra_health")
    graph.add_edge("infra_health", "log_analysis")
    graph.add_edge("log_analysis", "metrics")
    graph.add_edge("metrics", "api_monitoring")
    graph.add_edge("api_monitoring", "incident_detection")
    graph.add_edge("incident_detection", "root_cause_analysis")
    graph.add_edge("root_cause_analysis", "recommendation")
    graph.add_edge("recommendation", "notification")
    graph.add_edge("notification", END)

    return graph.compile()


# Compiled once, reused for every /api/workflow/run call
guardian_graph = build_graph()


async def execute_workflow(trigger: str = "manual", target_service_id: str | None = None) -> dict:
    """Runs the full LangGraph pipeline and returns a WorkflowRun-shaped dict."""
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    started_at = datetime.now(timezone.utc).isoformat()

    initial_state: AgentState = {
        "run_id": run_id,
        "trigger": trigger,
        "target_service_id": target_service_id,
        "steps": [],
    }

    final_state = guardian_graph.invoke(initial_state)

    finished_at = datetime.now(timezone.utc).isoformat()
    steps = final_state.get("steps", [])
    duration_ms = sum(s.get("duration_ms", 0) for s in steps)
    incidents = final_state.get("detected_incidents", [])

    run = {
        "run_id": run_id,
        "trigger": trigger,
        "status": "success",
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "steps": steps,
        "incidents_detected": len(incidents),
        "recommendations_generated": len(final_state.get("recommendations", {})),
        "summary": (
            f"Workflow completed across {len(steps)} agents. "
            f"{len(incidents)} new incident(s) detected and analyzed."
        ),
    }
    return run
