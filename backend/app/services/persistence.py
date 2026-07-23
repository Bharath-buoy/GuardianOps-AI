"""
MongoDB Persistence Layer
============================
Write-through helpers that mirror in-memory `store` changes into MongoDB
Atlas collections (users, services, metrics, logs, incidents,
workflow_runs, recommendations) whenever a real connection is available.

These are intentionally "best-effort": if Mongo is unreachable, every
function here silently no-ops (the in-memory store, which every router
already reads from, remains fully functional either way — see
app/core/database.py's connection fallback strategy).
"""
import logging

from app.core.database import get_collection

logger = logging.getLogger("guardianops.persistence")


async def persist_workflow_run(run: dict) -> None:
    collection = get_collection("workflow_runs")
    if collection is None:
        return
    try:
        await collection.update_one({"run_id": run["run_id"]}, {"$set": run}, upsert=True)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to persist workflow run %s", run.get("run_id"))


async def persist_incident(incident: dict) -> None:
    collection = get_collection("incidents")
    if collection is None:
        return
    try:
        await collection.update_one(
            {"incident_id": incident["incident_id"]}, {"$set": incident}, upsert=True
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to persist incident %s", incident.get("incident_id"))


async def persist_service(service: dict) -> None:
    collection = get_collection("services")
    if collection is None:
        return
    try:
        await collection.update_one(
            {"service_id": service["service_id"]}, {"$set": service}, upsert=True
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to persist service %s", service.get("service_id"))


async def persist_logs(entries: list[dict]) -> None:
    collection = get_collection("logs")
    if collection is None or not entries:
        return
    try:
        await collection.insert_many([dict(e) for e in entries], ordered=False)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to persist %d log entr(y/ies)", len(entries))


async def persist_metric_point(service_id: str, point: dict) -> None:
    collection = get_collection("metrics")
    if collection is None:
        return
    try:
        await collection.insert_one({"service_id": service_id, **point})
    except Exception:  # noqa: BLE001
        logger.exception("Failed to persist metric point for %s", service_id)


async def persist_recommendation(recommendation: dict) -> None:
    collection = get_collection("recommendations")
    if collection is None:
        return
    try:
        await collection.update_one(
            {"incident_id": recommendation["incident_id"]}, {"$set": recommendation}, upsert=True
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to persist recommendation for %s", recommendation.get("incident_id"))


async def persist_agent(agent: dict) -> None:
    """Write-through for the Guardian Agent registry (see /guardian-agent) —
    upserted on every telemetry post so `last_seen` stays current in Mongo."""
    collection = get_collection("agents")
    if collection is None:
        return
    try:
        await collection.update_one({"agent_id": agent["agent_id"]}, {"$set": agent}, upsert=True)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to persist Guardian Agent %s", agent.get("agent_id"))
