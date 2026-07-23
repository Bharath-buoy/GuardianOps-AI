"""
GuardianOps AI - FastAPI Application Entrypoint
=================================================
AI-Powered Multi-Agent Digital Infrastructure Monitoring & Incident
Intelligence Platform.

Run with:
    uvicorn app.main:app --reload
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo, database
from app.core.deps import get_current_user
from app.routers import (
    agents,
    analytics,
    analyze,
    auth,
    dashboard,
    incidents,
    infrastructure,
    logs,
    metrics,
    recommendations,
    workflow,
)
from app.services.log_watcher import log_watcher
from app.services.mock_data import store
from app.services.persistence import persist_logs
from app.services.scheduler import scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
logger = logging.getLogger("guardianops.main")

_simulation_task: asyncio.Task | None = None


async def _simulation_loop() -> None:
    """Background task that keeps mock telemetry 'alive' while the server runs."""
    while True:
        try:
            store.tick()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Simulation tick failed: %s", exc)
        await asyncio.sleep(settings.SIMULATION_TICK_SECONDS)


def _make_log_entry_callback(main_loop: asyncio.AbstractEventLoop):
    """The watchdog observer runs on its own background thread, so new log
    entries are folded into the shared store synchronously (thread-safe
    under the GIL for simple dict/list appends) and any MongoDB write is
    scheduled back onto the main asyncio event loop."""

    def _on_new_entries(entries: list[dict]) -> None:
        store.ingest_log_entries(entries)
        if database.connected:
            asyncio.run_coroutine_threadsafe(persist_logs(entries), main_loop)

    return _on_new_entries


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _simulation_task
    logger.info("🚀 Starting %s (%s mode)", settings.APP_NAME, settings.APP_ENV)
    await connect_to_mongo()

    if settings.USE_MOCK_DATA:
        _simulation_task = asyncio.create_task(_simulation_loop())
        logger.info("🟢 Mock telemetry simulation loop started (tick every %ss)", settings.SIMULATION_TICK_SECONDS)

    if settings.LIVE_MONITORING:
        main_loop = asyncio.get_running_loop()
        log_watcher.on_new_entries = _make_log_entry_callback(main_loop)
        log_watcher.start(settings.LOGS_DIR)
        scheduler.start()
        logger.info(
            "🩺 Live monitoring enabled — watching %s and running the AI workflow every %ss",
            settings.LOGS_DIR,
            settings.SCHEDULER_INTERVAL_SECONDS,
        )

    yield

    if _simulation_task:
        _simulation_task.cancel()
    if settings.LIVE_MONITORING:
        log_watcher.stop()
        scheduler.stop()
    await close_mongo_connection()
    logger.info("👋 GuardianOps AI shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Multi-Agent Digital Infrastructure Monitoring & Incident Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routes are intentionally NOT behind get_current_user (register/login
# are how a token is obtained in the first place).
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)

# Every other API route requires a valid JWT — GuardianOps AI is a
# single-operator AIOps console, not a public dashboard. Applying the
# dependency here (rather than editing every router file) protects all
# existing endpoints without changing their internal implementation.
_protected = [Depends(get_current_user)]
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX, dependencies=_protected)
app.include_router(infrastructure.router, prefix=settings.API_V1_PREFIX, dependencies=_protected)
app.include_router(incidents.router, prefix=settings.API_V1_PREFIX, dependencies=_protected)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX, dependencies=_protected)
app.include_router(analyze.router, prefix=settings.API_V1_PREFIX, dependencies=_protected)
app.include_router(workflow.router, prefix=settings.API_V1_PREFIX, dependencies=_protected)
app.include_router(metrics.router, prefix=settings.API_V1_PREFIX, dependencies=_protected)
app.include_router(logs.router, prefix=settings.API_V1_PREFIX, dependencies=_protected)
app.include_router(recommendations.router, prefix=settings.API_V1_PREFIX, dependencies=_protected)

# Guardian Agent router is intentionally NOT behind the blanket `_protected`
# (user JWT) dependency: its GET /agents route requires a user JWT while its
# POST /agents/telemetry route requires an agent API key instead — each
# route declares its own Depends(...) internally (see app/routers/agents.py).
app.include_router(agents.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "tagline": "AI-Powered Multi-Agent Digital Infrastructure Monitoring & Incident Intelligence Platform",
        "status": "online",
        "mongodb_connected": database.connected,
        "live_monitoring": settings.LIVE_MONITORING,
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "mongodb_connected": database.connected,
        "mock_data_mode": settings.USE_MOCK_DATA,
        "live_monitoring": settings.LIVE_MONITORING,
        "services_tracked": len(store.services),
    }
