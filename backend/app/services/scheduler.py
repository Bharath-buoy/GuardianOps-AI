"""
GuardianOps AI Scheduler
==========================
Runs the full LangGraph multi-agent workflow on a fixed interval
(default: every 30 seconds, per settings.SCHEDULER_INTERVAL_SECONDS),
driven by real psutil metrics and real application logs (rather than a
person clicking "Run Workflow" manually every time).

This complements — and reuses — the existing manual workflow.run endpoint
and the existing mock telemetry simulation loop; all three can run
side-by-side without conflict since they all operate on the same shared
`store` singleton.
"""
import asyncio
import logging

from app.agents.graph import execute_workflow
from app.core.config import settings
from app.services.mock_data import store
from app.services.persistence import persist_workflow_run

logger = logging.getLogger("guardianops.scheduler")


class GuardianScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    async def _loop(self) -> None:
        self._running = True
        logger.info(
            "🕒 GuardianOps AI scheduler started — running the LangGraph workflow every %ss",
            settings.SCHEDULER_INTERVAL_SECONDS,
        )
        while self._running:
            try:
                run = await execute_workflow(trigger="scheduled")
                store.add_workflow_run(run)
                await persist_workflow_run(run)
                if run["incidents_detected"] > 0:
                    logger.info(
                        "🔎 Scheduled run %s detected %d new incident(s)",
                        run["run_id"],
                        run["incidents_detected"],
                    )
            except Exception:  # noqa: BLE001
                logger.exception("Scheduled workflow run failed")
            await asyncio.sleep(settings.SCHEDULER_INTERVAL_SECONDS)

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None


scheduler = GuardianScheduler()
