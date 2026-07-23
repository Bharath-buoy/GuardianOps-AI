"""
Guardian Agent endpoints (see /guardian-agent).

Two distinct auth models on purpose:
  - POST /agents/telemetry  -> API key (a standalone agent isn't a logged-in user)
  - GET  /agents             -> user JWT (same as every other dashboard endpoint)

Each route declares its own Depends(...) rather than relying on a blanket
router-level dependency, since the two routes intentionally require
different credentials.
"""
import logging
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.core.agent_auth import verify_agent_api_key
from app.core.deps import get_current_user
from app.models.guardian_agent import GuardianAgentTelemetryAck, GuardianAgentTelemetryIn
from app.services.log_parser import parse_log_batch
from app.services.mock_data import store
from app.services.persistence import persist_agent, persist_logs, persist_service

logger = logging.getLogger("guardianops.agents")

router = APIRouter(prefix="/agents", tags=["Guardian Agents"])


@router.get("")
async def list_agents(_current_user: dict = Depends(get_current_user)):
    """Lists every Guardian Agent that has ever sent telemetry, with a
    computed `online` flag — consumed by the existing dashboard/Infrastructure
    views (no new frontend page required; agents surface as regular services
    tagged 'agent')."""
    agents = store.get_agents()
    return {
        "total": len(agents),
        "online": sum(1 for a in agents if a["online"]),
        "agents": agents,
    }


@router.post("/telemetry", response_model=GuardianAgentTelemetryAck)
async def ingest_telemetry(
    payload: GuardianAgentTelemetryIn,
    _api_key: str = Depends(verify_agent_api_key),
):
    """
    Ingests a telemetry batch from a standalone Guardian Agent.

    Pipeline: register/touch the agent -> fold its psutil-shaped metrics into
    the shared store (same schema as the local host-system service) -> parse
    + ingest any raw log lines it forwarded -> best-effort persist to Mongo.
    Nothing here talks to LangGraph directly — the existing scheduler (every
    SCHEDULER_INTERVAL_SECONDS) and the manual "Run Workflow" button already
    pick up any 'live'-tagged service on their next pass, so agent telemetry
    flows into incident detection automatically without further wiring.
    """
    agent = store.register_or_touch_agent(payload.agent_id, payload.hostname, payload.os)
    await persist_agent(agent)

    metrics_ingested = False
    if payload.metrics is not None:
        service_id = store.apply_agent_metrics(payload.agent_id, payload.hostname, payload.metrics.model_dump())
        metrics_ingested = True
        service = store.services.get(service_id)
        if service:
            await persist_service(service)

    logs_ingested = 0
    if payload.logs:
        grouped: dict[str, list[str]] = defaultdict(list)
        for entry in payload.logs:
            grouped[entry.service_id].append(entry.line)

        all_parsed: list[dict] = []
        for service_id, lines in grouped.items():
            parsed = parse_log_batch(lines, default_service=service_id)
            all_parsed.extend(parsed)

        if all_parsed:
            store.ingest_log_entries(all_parsed)
            await persist_logs(all_parsed)
            logs_ingested = len(all_parsed)

    logger.info(
        "📡 Telemetry received from Guardian Agent %s (%s) — metrics=%s, logs=%d",
        payload.agent_id,
        payload.hostname,
        metrics_ingested,
        logs_ingested,
    )

    return GuardianAgentTelemetryAck(
        accepted=True,
        agent_id=payload.agent_id,
        metrics_ingested=metrics_ingested,
        logs_ingested=logs_ingested,
        server_time=datetime.now(timezone.utc).isoformat(),
    )
