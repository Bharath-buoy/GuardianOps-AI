"""
Mock Infrastructure Data Generator
==================================
GuardianOps AI simulates a realistic enterprise digital infrastructure so the
platform can be demoed end-to-end without needing real collectors wired up
to production systems. Data is generated deterministically at boot and then
"drifts" on every simulation tick to feel alive (CPU/RAM/latency jitter,
occasional degradations, occasional incidents).

This module is intentionally the single source of truth for in-memory state.
Routers read/write through here; if MongoDB is connected, state is also
persisted so history survives restarts.
"""
import random
import re
import uuid
from datetime import datetime, timedelta, timezone

from app.core.config import settings

random.seed(42)  # reproducible demo data on first boot

SERVICE_CATALOG = [
    {"name": "auth-service", "type": "microservice", "tags": ["core", "identity"]},
    {"name": "payment-gateway-api", "type": "api", "tags": ["core", "payments"]},
    {"name": "user-profile-service", "type": "microservice", "tags": ["core"]},
    {"name": "notification-service", "type": "microservice", "tags": ["messaging"]},
    {"name": "order-processing-service", "type": "microservice", "tags": ["core", "commerce"]},
    {"name": "inventory-api", "type": "api", "tags": ["commerce"]},
    {"name": "search-service", "type": "microservice", "tags": ["discovery"]},
    {"name": "recommendation-engine", "type": "microservice", "tags": ["ai", "discovery"]},
    {"name": "postgres-primary-db", "type": "database", "tags": ["storage", "critical"]},
    {"name": "mongo-analytics-db", "type": "database", "tags": ["storage"]},
    {"name": "redis-cache-cluster", "type": "cache", "tags": ["storage", "performance"]},
    {"name": "rabbitmq-broker", "type": "queue", "tags": ["messaging"]},
    {"name": "api-gateway", "type": "api", "tags": ["core", "edge"]},
    {"name": "billing-service", "type": "microservice", "tags": ["core", "payments"]},
    {"name": "media-storage-container", "type": "container", "tags": ["storage"]},
    {"name": "reporting-service", "type": "microservice", "tags": ["analytics"]},
    {"name": "web-frontend-container", "type": "container", "tags": ["edge"]},
    {"name": "shipping-integration-api", "type": "api", "tags": ["commerce", "external"]},
]

REGIONS = ["ap-south-1", "us-east-1", "eu-west-1"]

INCIDENT_TEMPLATES = [
    {
        "title": "Elevated latency on {service}",
        "summary": "The Incident Detection Agent observed p95 latency exceeding the "
        "adaptive threshold on {service} for 3 consecutive intervals.",
        "root_cause": "Root Cause Analysis Agent correlated the latency spike with a "
        "connection pool saturation event and a concurrent spike in upstream "
        "request volume ({rps} req/min).",
        "recommendation": "Scale {service} horizontally by 2 replicas and raise the "
        "database connection pool ceiling from 50 to 100 to absorb burst traffic.",
        "severity": "medium",
    },
    {
        "title": "High error rate detected on {service}",
        "summary": "API Monitoring Agent flagged a sustained 5xx error rate of "
        "{error_rate}% on {service}, breaching the 2% SLO.",
        "root_cause": "Log Analysis Agent traced repeated stack traces to a null "
        "reference exception introduced in the last deployment of {service}.",
        "recommendation": "Roll back {service} to the previous stable release "
        "(v-1) and schedule a hotfix for the null-check regression.",
        "severity": "high",
    },
    {
        "title": "CPU saturation on {service}",
        "summary": "Metrics Agent detected CPU utilization above 90% on {service} "
        "sustained for over 5 minutes.",
        "root_cause": "Root Cause Analysis Agent identified an inefficient N+1 query "
        "pattern triggered by a batch job overlapping with peak traffic.",
        "recommendation": "Introduce query batching/caching for the offending "
        "endpoint and move the batch job to an off-peak schedule.",
        "severity": "medium",
    },
    {
        "title": "Memory pressure on {service}",
        "summary": "Infrastructure Health Agent reported RAM usage above 88% with a "
        "rising trend on {service}, risking OOM termination.",
        "root_cause": "Root Cause Analysis Agent traced the leak to an unbounded "
        "in-memory cache that is never evicted under sustained load.",
        "recommendation": "Add an LRU eviction policy with a max size bound and "
        "redeploy with a memory limit alert at 80%.",
        "severity": "high",
    },
    {
        "title": "Service unavailability: {service}",
        "summary": "Uptime probe failures on {service} triggered a critical page; "
        "the service failed 4 consecutive health checks.",
        "root_cause": "Root Cause Analysis Agent correlated the outage with a "
        "downstream dependency ({dependency}) timing out during a deploy window.",
        "recommendation": "Add circuit breaker + retry-with-backoff around the "
        "{dependency} client and stagger deploy windows to avoid overlap.",
        "severity": "critical",
    },
    {
        "title": "Connection pool exhaustion on {service}",
        "summary": "Database Agent observed connection pool utilization at 100% "
        "on {service}, causing request queuing.",
        "root_cause": "Root Cause Analysis Agent found long-running transactions "
        "holding connections open due to a missing timeout configuration.",
        "recommendation": "Set an explicit statement_timeout and increase the pool "
        "size with PgBouncer in transaction pooling mode.",
        "severity": "medium",
    },
]

LOG_LEVELS = ["INFO", "INFO", "INFO", "WARN", "ERROR", "DEBUG"]
LOG_MESSAGES = {
    "INFO": [
        "Request completed successfully in {ms}ms",
        "Health check passed",
        "Cache hit ratio at {pct}%",
        "Scheduled job '{job}' completed",
        "New connection established from pool",
    ],
    "WARN": [
        "Response time {ms}ms exceeds SLA threshold",
        "Retrying request after transient failure (attempt {n}/3)",
        "Connection pool utilization at {pct}%",
        "Deprecated endpoint accessed: /v1/legacy",
    ],
    "ERROR": [
        "Unhandled exception: NullReferenceException at handler",
        "Database query timeout after {ms}ms",
        "Failed to reach downstream dependency: timeout",
        "5xx response returned to client",
    ],
    "DEBUG": [
        "Trace id {trace} propagated to downstream span",
        "Payload size: {kb}KB",
        "Feature flag '{flag}' evaluated to true",
    ],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _rand_status(weighted: bool = True) -> str:
    if weighted:
        return random.choices(
            ["healthy", "healthy", "healthy", "healthy", "degraded", "critical"],
            weights=[45, 25, 10, 5, 10, 5],
        )[0]
    return random.choice(["healthy", "degraded", "critical", "offline"])


class MockDataStore:
    """In-memory store simulating the entire GuardianOps AI infrastructure."""

    def __init__(self) -> None:
        self.services: dict[str, dict] = {}
        self.incidents: dict[str, dict] = {}
        self.metrics_history: dict[str, list[dict]] = {}
        self.logs: list[dict] = []
        self.workflow_runs: dict[str, dict] = {}
        self.recommendations: dict[str, dict] = {}
        # Live-monitoring extensions (real psutil data)
        self.latest_system_snapshot: dict = {}
        self.system_metrics_history: list[dict] = []
        # Standalone Guardian Agent registry (see /guardian-agent) — keyed by agent_id
        self.agents: dict[str, dict] = {}
        self._bootstrap()

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------
    def _bootstrap(self) -> None:
        count = min(settings.MOCK_SERVICE_COUNT, len(SERVICE_CATALOG))
        catalog = SERVICE_CATALOG[:count]
        for entry in catalog:
            self._create_service(entry)

        # Seed metrics history (last 24h, 5 min interval)
        for service_id in self.services:
            self._seed_metrics_history(service_id)

        # Seed logs (last ~500 lines)
        for _ in range(500):
            self._generate_log_line(persist_time_jitter=True)
        self.logs.sort(key=lambda l: l["timestamp"])

        # Seed a handful of historical incidents
        for _ in range(9):
            self._create_incident(historical=True)

        # Seed a couple of workflow run history entries
        for _ in range(6):
            self._create_workflow_run_history()

    def _create_service(self, entry: dict) -> dict:
        service_id = entry["name"]
        status = _rand_status()
        cpu = round(random.uniform(15, 55), 1) if status == "healthy" else round(random.uniform(70, 95), 1)
        ram = round(random.uniform(20, 60), 1) if status == "healthy" else round(random.uniform(75, 92), 1)
        latency = round(random.uniform(20, 120), 1) if status == "healthy" else round(random.uniform(200, 900), 1)
        error_rate = round(random.uniform(0, 1.2), 2) if status == "healthy" else round(random.uniform(2, 12), 2)
        uptime = round(random.uniform(99.5, 99.99), 3) if status == "healthy" else round(random.uniform(95.0, 99.2), 3)

        service = {
            "service_id": service_id,
            "name": service_id,
            "type": entry["type"],
            "status": status,
            "environment": "production",
            "region": random.choice(REGIONS),
            "uptime_percent": uptime,
            "latency_ms": latency,
            "cpu_percent": cpu,
            "ram_percent": ram,
            "error_rate_percent": error_rate,
            "requests_per_min": random.randint(120, 8000),
            "version": f"v{random.randint(1, 4)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "last_deployed": _iso(datetime.now(timezone.utc) - timedelta(days=random.randint(0, 21))),
            "tags": entry["tags"],
            "dependencies": [],
        }
        self.services[service_id] = service
        return service

    def _seed_metrics_history(self, service_id: str, hours: int = 24, interval_minutes: int = 5) -> None:
        points = []
        now = datetime.now(timezone.utc)
        base_cpu = random.uniform(25, 45)
        base_ram = random.uniform(30, 50)
        base_latency = random.uniform(40, 100)
        steps = int((hours * 60) / interval_minutes)
        for i in range(steps, 0, -1):
            ts = now - timedelta(minutes=i * interval_minutes)
            jitter = random.uniform(-8, 8)
            spike = 25 if random.random() < 0.03 else 0
            points.append(
                {
                    "service_id": service_id,
                    "timestamp": _iso(ts),
                    "cpu_percent": round(max(2, min(99, base_cpu + jitter + spike)), 1),
                    "ram_percent": round(max(5, min(99, base_ram + jitter * 0.6 + spike * 0.4)), 1),
                    "latency_ms": round(max(5, base_latency + jitter * 3 + spike * 6), 1),
                    "error_rate_percent": round(max(0, random.uniform(0, 1.5) + (spike * 0.15)), 2),
                    "requests_per_min": random.randint(100, 6000),
                }
            )
        self.metrics_history[service_id] = points

    def _generate_log_line(self, persist_time_jitter: bool = False) -> dict:
        service_id = random.choice(list(self.services.keys()))
        level = random.choice(LOG_LEVELS)
        template = random.choice(LOG_MESSAGES[level])
        message = template.format(
            ms=random.randint(15, 950),
            pct=random.randint(40, 99),
            job=random.choice(["nightly-aggregation", "cache-warmup", "report-export"]),
            n=random.randint(1, 3),
            trace=uuid.uuid4().hex[:12],
            kb=random.randint(1, 512),
            flag=random.choice(["new-checkout-flow", "beta-search-ranking", "dark-mode"]),
        )
        ts = datetime.now(timezone.utc)
        if persist_time_jitter:
            ts = ts - timedelta(minutes=random.randint(0, 1440))
        entry = {
            "log_id": str(uuid.uuid4()),
            "service_id": service_id,
            "level": level,
            "message": message,
            "timestamp": _iso(ts),
        }
        self.logs.append(entry)
        return entry

    def _create_incident(self, historical: bool = False) -> dict:
        template = random.choice(INCIDENT_TEMPLATES)
        service = random.choice(list(self.services.values()))
        dependency = random.choice([s for s in self.services if s != service["service_id"]] or [service["service_id"]])
        created = datetime.now(timezone.utc) - timedelta(
            hours=random.randint(1, 96) if historical else 0,
            minutes=random.randint(0, 59),
        )
        severity = template["severity"]
        status = random.choice(["resolved", "resolved", "monitoring", "investigating"]) if historical else "open"
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

        summary = template["summary"].format(
            service=service["name"], error_rate=service["error_rate_percent"]
        )
        root_cause = template["root_cause"].format(
            service=service["name"], rps=service["requests_per_min"], dependency=dependency
        )
        recommendation = template["recommendation"].format(service=service["name"], dependency=dependency)

        timeline = [
            {
                "timestamp": _iso(created),
                "label": "Detected",
                "description": f"Incident Detection Agent flagged anomaly on {service['name']}.",
                "actor": "Incident Detection Agent",
            },
            {
                "timestamp": _iso(created + timedelta(minutes=2)),
                "label": "Root Cause Analysis",
                "description": root_cause,
                "actor": "Root Cause Analysis Agent",
            },
            {
                "timestamp": _iso(created + timedelta(minutes=4)),
                "label": "Recommendation Generated",
                "description": recommendation,
                "actor": "Recommendation Agent",
            },
        ]
        resolved_at = None
        if status == "resolved":
            resolved_at = _iso(created + timedelta(minutes=random.randint(15, 240)))
            timeline.append(
                {
                    "timestamp": resolved_at,
                    "label": "Resolved",
                    "description": f"{service['name']} returned to healthy status after remediation.",
                    "actor": "Notification Agent",
                }
            )

        incident = {
            "incident_id": incident_id,
            "title": template["title"].format(service=service["name"]),
            "severity": severity,
            "status": status,
            "affected_services": [service["service_id"]],
            "ai_summary": summary,
            "root_cause": root_cause,
            "recommendation": recommendation,
            "confidence_score": round(random.uniform(0.78, 0.98), 2),
            "created_at": _iso(created),
            "updated_at": _iso(created + timedelta(minutes=4)),
            "resolved_at": resolved_at,
            "timeline": timeline,
            "detected_by": "Incident Detection Agent",
            "tags": service["tags"],
        }
        self.incidents[incident_id] = incident

        self.recommendations[incident_id] = {
            "incident_id": incident_id,
            "recommendation": recommendation,
            "confidence_score": incident["confidence_score"],
            "generated_at": incident["updated_at"],
            "actions": [
                recommendation,
                f"Add alerting rule to catch recurrence on {service['name']} earlier.",
                "Document remediation steps in the runbook.",
            ],
        }
        return incident

    def _create_workflow_run_history(self) -> dict:
        from app.agents.state import AGENT_SEQUENCE  # local import to avoid cycle

        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        started = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))
        steps = []
        cursor = started
        for agent_id, agent_name in AGENT_SEQUENCE:
            duration = random.randint(150, 900)
            cursor = cursor + timedelta(milliseconds=duration)
            steps.append(
                {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "status": "success",
                    "started_at": _iso(cursor - timedelta(milliseconds=duration)),
                    "finished_at": _iso(cursor),
                    "duration_ms": duration,
                    "output_summary": f"{agent_name} completed analysis pass.",
                    "details": {},
                }
            )
        finished = cursor
        run = {
            "run_id": run_id,
            "trigger": random.choice(["scheduled", "manual", "auto-triggered"]),
            "status": "success",
            "started_at": _iso(started),
            "finished_at": _iso(finished),
            "duration_ms": int((finished - started).total_seconds() * 1000),
            "steps": steps,
            "incidents_detected": random.randint(0, 2),
            "recommendations_generated": random.randint(0, 2),
            "summary": "Full workflow cycle completed successfully across all 8 agents.",
        }
        self.workflow_runs[run_id] = run
        return run

    # ------------------------------------------------------------------
    # Live simulation tick (called by background task)
    # ------------------------------------------------------------------
    def tick(self) -> None:
        for service in self.services.values():
            drift = random.uniform(-6, 6)
            service["cpu_percent"] = round(max(2, min(99, service["cpu_percent"] + drift)), 1)
            service["ram_percent"] = round(max(5, min(99, service["ram_percent"] + drift * 0.5)), 1)
            service["latency_ms"] = round(max(5, service["latency_ms"] + drift * 4), 1)
            service["error_rate_percent"] = round(max(0, service["error_rate_percent"] + drift * 0.05), 2)
            service["requests_per_min"] = max(50, service["requests_per_min"] + random.randint(-200, 200))

            if service["cpu_percent"] > 85 or service["error_rate_percent"] > 5:
                service["status"] = "critical"
            elif service["cpu_percent"] > 70 or service["error_rate_percent"] > 2:
                service["status"] = "degraded"
            else:
                service["status"] = "healthy"

            history = self.metrics_history.setdefault(service["service_id"], [])
            history.append(
                {
                    "service_id": service["service_id"],
                    "timestamp": _now_iso(),
                    "cpu_percent": service["cpu_percent"],
                    "ram_percent": service["ram_percent"],
                    "latency_ms": service["latency_ms"],
                    "error_rate_percent": service["error_rate_percent"],
                    "requests_per_min": service["requests_per_min"],
                }
            )
            if len(history) > 500:
                del history[0]

        for _ in range(random.randint(1, 4)):
            self._generate_log_line()
        if len(self.logs) > 2000:
            del self.logs[: len(self.logs) - 2000]

        # Small chance of a fresh incident
        if random.random() < 0.06:
            self._create_incident(historical=False)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    def get_services(self) -> list[dict]:
        return list(self.services.values())

    def get_service(self, service_id: str) -> dict | None:
        return self.services.get(service_id)

    def get_incidents(self, status: str | None = None, severity: str | None = None) -> list[dict]:
        items = list(self.incidents.values())
        if status:
            items = [i for i in items if i["status"] == status]
        if severity:
            items = [i for i in items if i["severity"] == severity]
        return sorted(items, key=lambda i: i["created_at"], reverse=True)

    def get_incident(self, incident_id: str) -> dict | None:
        return self.incidents.get(incident_id)

    def get_logs(self, service_id: str | None = None, level: str | None = None, limit: int = 200) -> list[dict]:
        items = self.logs
        if service_id:
            items = [l for l in items if l["service_id"] == service_id]
        if level:
            items = [l for l in items if l["level"] == level]
        return sorted(items, key=lambda l: l["timestamp"], reverse=True)[:limit]

    def get_metrics(self, service_id: str | None = None) -> dict[str, list[dict]]:
        if service_id:
            return {service_id: self.metrics_history.get(service_id, [])}
        return self.metrics_history

    def get_workflow_runs(self, limit: int = 20) -> list[dict]:
        return sorted(self.workflow_runs.values(), key=lambda r: r["started_at"], reverse=True)[:limit]

    def add_workflow_run(self, run: dict) -> None:
        self.workflow_runs[run["run_id"]] = run

    def add_incident(self, incident: dict) -> None:
        self.incidents[incident["incident_id"]] = incident

    def summary_counts(self) -> dict:
        services = self.get_services()
        healthy = sum(1 for s in services if s["status"] == "healthy")
        degraded = sum(1 for s in services if s["status"] == "degraded")
        critical = sum(1 for s in services if s["status"] == "critical")
        offline = sum(1 for s in services if s["status"] == "offline")
        return {
            "total": len(services),
            "healthy": healthy,
            "degraded": degraded,
            "critical": critical,
            "offline": offline,
        }

    # ------------------------------------------------------------------
    # Live monitoring extensions
    # ------------------------------------------------------------------
    # Everything below is additive: it lets real psutil metrics and real,
    # watchdog-tailed application logs flow into the SAME store/schema the
    # existing routers and frontend already consume, so no existing
    # functionality changes shape — only the data source does.

    def ensure_service_registered(self, service_id: str, service_type: str = "microservice", tags: list[str] | None = None) -> dict:
        """Auto-registers a service the first time real logs/metrics reference it."""
        if service_id in self.services:
            return self.services[service_id]
        service = {
            "service_id": service_id,
            "name": service_id,
            "type": service_type,
            "status": "healthy",
            "environment": "production",
            "region": random.choice(REGIONS),
            "uptime_percent": 100.0,
            "latency_ms": 0.0,
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "error_rate_percent": 0.0,
            "requests_per_min": 0,
            "version": "live",
            "last_deployed": _now_iso(),
            "tags": (tags or []) + ["live"],
            "dependencies": [],
        }
        self.services[service_id] = service
        self.metrics_history.setdefault(service_id, [])
        return service

    def ingest_log_entries(self, entries: list[dict]) -> None:
        """Feeds real, watchdog-tailed log entries into the shared log store
        and auto-registers/updates the health of the service they reference."""
        for entry in entries:
            service_id = entry.get("service_id", "unknown-service")
            self.ensure_service_registered(service_id)
            self.logs.append(entry)
        if len(self.logs) > 3000:
            del self.logs[: len(self.logs) - 3000]

        touched = {e.get("service_id") for e in entries if e.get("service_id")}
        for service_id in touched:
            self.recompute_service_health_from_logs(service_id)

    def recompute_service_health_from_logs(self, service_id: str, window: int = 50) -> None:
        """Derives an error rate / status for a service from its most recent
        real log lines (rather than random simulation drift)."""
        service = self.services.get(service_id)
        if not service:
            return
        recent = self.get_logs(service_id=service_id, limit=window)
        if not recent:
            return
        error_count = sum(1 for l in recent if l["level"] == "ERROR")
        warn_count = sum(1 for l in recent if l["level"] == "WARN")
        error_rate = round(100 * error_count / len(recent), 2)

        service["error_rate_percent"] = error_rate
        service["requests_per_min"] = max(service.get("requests_per_min", 0), len(recent) * 2)

        if error_rate > 8 or error_count >= 5:
            service["status"] = "critical"
        elif error_rate > 2 or warn_count >= 5:
            service["status"] = "degraded"
        else:
            service["status"] = "healthy"

    def apply_system_metrics(self, snapshot: dict) -> None:
        """Folds a real psutil system snapshot into a dedicated 'host-system'
        pseudo-service entry (visible in Infrastructure like any other
        service) and appends it to that service's metrics history so the
        existing charts work unmodified."""
        self._apply_metrics_snapshot("host-system", snapshot, tags=["infrastructure", "host"])

    def _apply_metrics_snapshot(self, service_id: str, snapshot: dict, tags: list[str] | None = None) -> None:
        """Shared by apply_system_metrics (local backend host) and
        apply_agent_metrics (remote Guardian Agents) — both feed a psutil-shaped
        snapshot into the same service/metrics-history schema so every existing
        router, chart, and the LangGraph live-detection path treat them
        identically regardless of where the data originated."""
        if "error" in snapshot:
            return
        service = self.ensure_service_registered(service_id, service_type="container", tags=tags)
        cpu_percent = snapshot["cpu"]["percent"]
        ram_percent = snapshot["ram"]["percent"]
        disk_percent = snapshot["disk"]["percent"]

        service["cpu_percent"] = cpu_percent
        service["ram_percent"] = ram_percent
        service["disk_percent"] = disk_percent
        service["latency_ms"] = round(snapshot["network"]["recv_kbps"] + snapshot["network"]["sent_kbps"], 1)
        service["requests_per_min"] = snapshot["process_count"]

        if cpu_percent > 90 or ram_percent > 90 or disk_percent > 92:
            service["status"] = "critical"
        elif cpu_percent > 75 or ram_percent > 80 or disk_percent > 85:
            service["status"] = "degraded"
        else:
            service["status"] = "healthy"

        history = self.metrics_history.setdefault(service_id, [])
        history.append(
            {
                "service_id": service_id,
                "timestamp": snapshot["timestamp"],
                "cpu_percent": cpu_percent,
                "ram_percent": ram_percent,
                "latency_ms": service["latency_ms"],
                "error_rate_percent": service["error_rate_percent"],
                "requests_per_min": service["requests_per_min"],
                "disk_percent": disk_percent,
            }
        )
        if len(history) > 500:
            del history[0]

        if service_id == "host-system":
            self.latest_system_snapshot = snapshot
            self.system_metrics_history.append(snapshot)
            if len(self.system_metrics_history) > 500:
                del self.system_metrics_history[0]

    # ------------------------------------------------------------------
    # Guardian Agent registry (standalone agents — see /guardian-agent)
    # ------------------------------------------------------------------
    @staticmethod
    def _agent_service_id(hostname: str) -> str:
        """Derives a stable, kebab-case service_id from an agent's hostname,
        e.g. 'DESKTOP-J3K9' -> 'agent-desktop-j3k9'. Prefixed so a Guardian
        Agent's host machine is unambiguous among other services/incidents,
        and distinct hostnames naturally map to distinct services — this is
        how multiple simultaneously-connected agents are supported."""
        slug = re.sub(r"[^a-z0-9]+", "-", hostname.strip().lower()).strip("-") or "unknown-host"
        return f"agent-{slug}"

    def register_or_touch_agent(self, agent_id: str, hostname: str, os_name: str) -> dict:
        """Registers a Guardian Agent on first contact, or updates its
        last_seen timestamp / metadata on every subsequent telemetry post."""
        now = _now_iso()
        service_id = self._agent_service_id(hostname)
        agent = self.agents.get(agent_id)
        if agent is None:
            agent = {
                "agent_id": agent_id,
                "hostname": hostname,
                "os": os_name,
                "service_id": service_id,
                "first_seen": now,
                "last_seen": now,
            }
            self.agents[agent_id] = agent
        else:
            agent["hostname"] = hostname
            agent["os"] = os_name
            agent["service_id"] = service_id
            agent["last_seen"] = now
        return agent

    def get_agents(self) -> list[dict]:
        """Returns registered Guardian Agents with a computed `online` flag
        (true if telemetry was received within AGENT_OFFLINE_AFTER_SECONDS)."""
        now = datetime.now(timezone.utc)
        result = []
        for agent in sorted(self.agents.values(), key=lambda a: a["last_seen"], reverse=True):
            try:
                last_seen_dt = datetime.fromisoformat(agent["last_seen"])
            except ValueError:
                last_seen_dt = now
            online = (now - last_seen_dt).total_seconds() <= settings.AGENT_OFFLINE_AFTER_SECONDS
            result.append({**agent, "online": online})
        return result

    def apply_agent_metrics(self, agent_id: str, hostname: str, snapshot: dict) -> str:
        """Feeds a remote Guardian Agent's psutil snapshot into the shared
        store, tagged as a 'live' service unique to that agent's host.
        Returns the service_id the metrics were recorded under."""
        service_id = self._agent_service_id(hostname)
        self._apply_metrics_snapshot(service_id, snapshot, tags=["agent", f"agent:{agent_id}"])
        return service_id

    def get_recommendations(self, limit: int = 50) -> list[dict]:
        items = sorted(self.recommendations.values(), key=lambda r: r["generated_at"], reverse=True)
        return items[:limit]

    def create_incident_from_detection(self, detection: dict, service_id: str, detected_by: str) -> dict:
        """Builds a schema-compatible Incident (matching the existing
        Incident model exactly) from a real-data detection produced by
        incident_rules.py / recommendation_engine.py, so it renders
        identically to simulated incidents in the existing frontend."""
        now = _now_iso()
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        timeline = [
            {
                "timestamp": now,
                "label": "Detected",
                "description": f"{detected_by} flagged an anomaly on {service_id} from live telemetry.",
                "actor": detected_by,
            },
            {
                "timestamp": now,
                "label": "Root Cause Analysis",
                "description": detection["root_cause"],
                "actor": "Root Cause Analysis Agent",
            },
            {
                "timestamp": now,
                "label": "Recommendation Generated",
                "description": detection["recommendation"],
                "actor": "Recommendation Agent",
            },
        ]
        incident = {
            "incident_id": incident_id,
            "title": detection["title"],
            "severity": detection["severity"],
            "status": "open",
            "affected_services": [service_id],
            "ai_summary": detection["summary"],
            "root_cause": detection["root_cause"],
            "recommendation": detection["recommendation"],
            "confidence_score": detection.get("confidence", 0.8),
            "created_at": now,
            "updated_at": now,
            "resolved_at": None,
            "timeline": timeline,
            "detected_by": detected_by,
            "tags": ["live"],
        }
        self.incidents[incident_id] = incident
        self.recommendations[incident_id] = {
            "incident_id": incident_id,
            "recommendation": detection["recommendation"],
            "confidence_score": incident["confidence_score"],
            "generated_at": now,
            "actions": [
                detection["recommendation"],
                f"Add alerting to catch recurrence on {service_id} earlier.",
            ],
        }
        return incident


# Singleton instance shared across the app
store = MockDataStore()
