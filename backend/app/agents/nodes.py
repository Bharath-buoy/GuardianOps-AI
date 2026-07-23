"""
GuardianOps AI - Agent Node Implementations
============================================
Each function below is a LangGraph node representing one specialized AI agent
in the multi-agent observability pipeline. Agents are deterministic/rule-based
by default (zero API key required) but are structured so a real LLM call
(OpenAI/Anthropic via LangChain) can be dropped into `_narrate()` when
USE_LLM=true, without touching the orchestration graph.
"""
import random
import time
from datetime import datetime, timedelta, timezone

from app.agents.state import AgentState
from app.core.config import settings
from app.services import incident_rules
from app.services.mock_data import store
from app.services.system_monitor import get_system_snapshot


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_step(state: AgentState, agent_id: str, agent_name: str, summary: str, details: dict | None = None) -> None:
    steps = state.setdefault("steps", [])
    steps.append(
        {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": "success",
            "started_at": _now(),
            "finished_at": _now(),
            "duration_ms": random.randint(120, 650),
            "output_summary": summary,
            "details": details or {},
        }
    )


def _narrate(rule_based_text: str) -> str:
    """
    Placeholder hook for optional LLM-generated narrative text.
    When settings.USE_LLM is True and an API key is present, this can be
    swapped for a real LangChain chat model call. Defaults to the
    deterministic rule-based text so the app runs with zero external keys.
    """
    if settings.USE_LLM and (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY):
        # Intentionally left as an extension point:
        # from langchain_openai import ChatOpenAI
        # llm = ChatOpenAI(model="gpt-4o-mini")
        # return llm.invoke(rule_based_text).content
        return rule_based_text
    return rule_based_text


# ----------------------------------------------------------------------
# 1. Infrastructure Health Agent
# ----------------------------------------------------------------------
def infrastructure_health_agent(state: AgentState) -> AgentState:
    # Live-monitoring extension: fold real psutil host metrics into the
    # store as a first-class "host-system" service before computing the
    # snapshot, so the health score reflects real infrastructure data too.
    # This is purely additive — simulated services are untouched.
    if settings.LIVE_MONITORING:
        try:
            snapshot = get_system_snapshot()
            store.apply_system_metrics(snapshot)
        except Exception:  # noqa: BLE001
            pass  # never let a real-metrics collection hiccup break the pipeline

    services = store.get_services()
    counts = store.summary_counts()
    health_score = round(
        100 * (counts["healthy"] + 0.5 * counts["degraded"]) / max(1, counts["total"]), 1
    )
    report = {
        "health_score": health_score,
        "counts": counts,
        "worst_services": sorted(services, key=lambda s: s["cpu_percent"], reverse=True)[:3],
    }
    state["services_snapshot"] = services
    state["infra_health_report"] = report
    _record_step(
        state,
        "infra-health",
        "Infrastructure Health Agent",
        f"Computed infrastructure health score: {health_score}/100 across {counts['total']} services.",
        {"health_score": health_score, "counts": counts},
    )
    return state


# ----------------------------------------------------------------------
# 2. Log Analysis Agent
# ----------------------------------------------------------------------
def log_analysis_agent(state: AgentState) -> AgentState:
    logs = store.get_logs(limit=300)
    error_logs = [l for l in logs if l["level"] == "ERROR"]
    warn_logs = [l for l in logs if l["level"] == "WARN"]
    by_service: dict[str, int] = {}
    for l in error_logs:
        by_service[l["service_id"]] = by_service.get(l["service_id"], 0) + 1
    top_offenders = sorted(by_service.items(), key=lambda kv: kv[1], reverse=True)[:3]

    # Live-monitoring extension: surface known problem patterns (db timeout,
    # connection failure, memory-leak hints) found in real ingested logs.
    # Additive-only key; existing consumers of `findings` are unaffected.
    pattern_hits = {}
    if settings.LIVE_MONITORING:
        for name, regex in incident_rules.LOG_PATTERNS.items():
            pattern_hits[name] = sum(1 for l in logs if regex.search(l.get("message", "")))

    findings = {
        "total_scanned": len(logs),
        "error_count": len(error_logs),
        "warn_count": len(warn_logs),
        "top_offenders": [{"service_id": s, "error_count": c} for s, c in top_offenders],
        "pattern_hits": pattern_hits,
    }
    state["log_findings"] = findings
    _record_step(
        state,
        "log-analysis",
        "Log Analysis Agent",
        f"Scanned {len(logs)} log lines — found {len(error_logs)} errors, {len(warn_logs)} warnings.",
        findings,
    )
    return state


# ----------------------------------------------------------------------
# 3. Metrics Agent
# ----------------------------------------------------------------------
def metrics_agent(state: AgentState) -> AgentState:
    services = state.get("services_snapshot", store.get_services())
    high_cpu = [s for s in services if s["cpu_percent"] > 75]
    high_ram = [s for s in services if s["ram_percent"] > 80]
    avg_latency = round(sum(s["latency_ms"] for s in services) / max(1, len(services)), 1)

    findings = {
        "avg_latency_ms": avg_latency,
        "high_cpu_services": [s["service_id"] for s in high_cpu],
        "high_ram_services": [s["service_id"] for s in high_ram],
    }
    state["metrics_findings"] = findings
    _record_step(
        state,
        "metrics",
        "Metrics Agent",
        f"Average latency {avg_latency}ms. Flagged {len(high_cpu)} high-CPU and {len(high_ram)} high-RAM services.",
        findings,
    )
    return state


# ----------------------------------------------------------------------
# 4. API Monitoring Agent
# ----------------------------------------------------------------------
def api_monitoring_agent(state: AgentState) -> AgentState:
    services = state.get("services_snapshot", store.get_services())
    apis = [s for s in services if s["type"] in ("api", "microservice")]
    breaching = [s for s in apis if s["error_rate_percent"] > 2 or s["latency_ms"] > 300]

    findings = {
        "apis_monitored": len(apis),
        "slo_breaches": [
            {"service_id": s["service_id"], "error_rate": s["error_rate_percent"], "latency_ms": s["latency_ms"]}
            for s in breaching
        ],
    }
    state["api_findings"] = findings
    _record_step(
        state,
        "api-monitoring",
        "API Monitoring Agent",
        f"Monitored {len(apis)} API/microservice endpoints — {len(breaching)} SLO breaches detected.",
        findings,
    )
    return state


# ----------------------------------------------------------------------
# 5. Incident Detection Agent
# ----------------------------------------------------------------------
def _has_recent_open_incident(service_id: str, title: str, window_minutes: int = 10) -> bool:
    """Prevents the scheduler (running every ~30s) from spamming duplicate
    incidents for the same still-ongoing real-world condition."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    for incident in store.incidents.values():
        if incident["title"] != title or service_id not in incident["affected_services"]:
            continue
        if incident["status"] == "resolved":
            continue
        try:
            created = datetime.fromisoformat(incident["created_at"])
        except ValueError:
            continue
        if created >= cutoff:
            return True
    return False


def _detect_live_incidents(state: AgentState) -> list[dict]:
    """Real-data detection path: evaluates services tagged 'live' (real
    sample apps + the host-system psutil service) against fixed thresholds
    and log patterns, producing incidents via the dynamic recommendation
    engine. Runs alongside — and does not replace — the simulated path
    below, so demo mode keeps working with zero live data configured."""
    services = state.get("services_snapshot", store.get_services())
    live_services = [s for s in services if "live" in s.get("tags", [])]
    created: list[dict] = []

    for service in live_services:
        detections = incident_rules.detect_metric_incidents(service)

        if service["service_id"] == "host-system" and store.latest_system_snapshot:
            net_kbps = (
                store.latest_system_snapshot.get("network", {}).get("sent_kbps", 0)
                + store.latest_system_snapshot.get("network", {}).get("recv_kbps", 0)
            )
            net_incident = incident_rules.detect_network_incident(service["service_id"], net_kbps)
            if net_incident:
                detections.append(net_incident)

        recent_logs = store.get_logs(service_id=service["service_id"], limit=50)
        detections.extend(incident_rules.detect_log_incidents(service["service_id"], recent_logs))

        for detection in detections:
            if _has_recent_open_incident(service["service_id"], detection["title"]):
                continue
            incident = store.create_incident_from_detection(
                detection, service["service_id"], detected_by="Incident Detection Agent (Live)"
            )
            created.append(incident)

    return created


def incident_detection_agent(state: AgentState) -> AgentState:
    new_incidents: list[dict] = []

    # Real-data path (real psutil metrics + real watched application logs)
    if settings.LIVE_MONITORING:
        new_incidents.extend(_detect_live_incidents(state))

    # Simulated demo path — preserved exactly as before so the platform
    # still demos convincingly with zero live data configured.
    services = state.get("services_snapshot", store.get_services())
    at_risk = [s for s in services if s["status"] in ("critical", "degraded") and "live" not in s.get("tags", [])]
    for s in at_risk[:2]:  # cap per run to keep demo readable
        if random.random() < 0.7:
            incident = store._create_incident(historical=False)  # noqa: SLF001
            new_incidents.append(incident)

    state["detected_incidents"] = new_incidents
    _record_step(
        state,
        "incident-detection",
        "Incident Detection Agent",
        f"Evaluated {len(at_risk)} at-risk services — created {len(new_incidents)} new incident(s).",
        {"incident_ids": [i["incident_id"] for i in new_incidents]},
    )
    return state


# ----------------------------------------------------------------------
# 6. Root Cause Analysis Agent
# ----------------------------------------------------------------------
def root_cause_analysis_agent(state: AgentState) -> AgentState:
    incidents = state.get("detected_incidents", [])
    reports = {}
    for incident in incidents:
        reports[incident["incident_id"]] = incident["root_cause"]
    state["root_cause_reports"] = reports
    _record_step(
        state,
        "root-cause-analysis",
        "Root Cause Analysis Agent",
        f"Generated root-cause analysis for {len(incidents)} incident(s).",
        {"incident_ids": list(reports.keys())},
    )
    return state


# ----------------------------------------------------------------------
# 7. Recommendation Agent
# ----------------------------------------------------------------------
def recommendation_agent(state: AgentState) -> AgentState:
    incidents = state.get("detected_incidents", [])
    recs = {}
    for incident in incidents:
        recs[incident["incident_id"]] = incident["recommendation"]
    state["recommendations"] = recs
    _record_step(
        state,
        "recommendation",
        "Recommendation Agent",
        f"Produced actionable recommendations for {len(incidents)} incident(s).",
        {"incident_ids": list(recs.keys())},
    )
    return state


# ----------------------------------------------------------------------
# 8. Notification Agent
# ----------------------------------------------------------------------
def notification_agent(state: AgentState) -> AgentState:
    incidents = state.get("detected_incidents", [])
    notifications = [
        {
            "incident_id": i["incident_id"],
            "channel": "dashboard",
            "message": f"New {i['severity']} incident: {i['title']}",
            "sent_at": _now(),
        }
        for i in incidents
    ]
    state["notifications_sent"] = notifications
    _record_step(
        state,
        "notification",
        "Notification Agent",
        f"Dispatched {len(notifications)} notification(s) to the dashboard feed.",
        {"count": len(notifications)},
    )
    return state
