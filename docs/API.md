# GuardianOps AI — REST API Reference

Base URL (local dev): `http://localhost:8000/api`

All responses are JSON. Every endpoint below except `/auth/register`, `/auth/login`,
`/auth/status`, and `/health` requires a valid JWT: `Authorization: Bearer <token>`.

---

## Authentication

### `POST /auth/register`

Registers the single GuardianOps AI operator account. Returns 409 if an account already exists.

```json
{ "name": "Jane Doe", "email": "jane@guardianops.ai", "password": "at-least-8-chars" }
```

Response: `{ "access_token": "...", "token_type": "bearer", "user": { ... } }`

### `POST /auth/login`

```json
{ "email": "jane@guardianops.ai", "password": "at-least-8-chars" }
```

Response: same shape as `/auth/register`.

### `GET /auth/me`

Returns the current authenticated user (requires JWT).

### `GET /auth/status`

Returns `{ "account_exists": true|false }` — used by the Register page to redirect to Login once
an account already exists.

---

## `GET /dashboard`

Returns aggregated data for the main dashboard view.

```json
{
  "health_score": 87.5,
  "service_counts": { "total": 14, "healthy": 10, "degraded": 3, "critical": 1, "offline": 0 },
  "kpis": {
    "avg_response_time_ms": 142.3,
    "avg_cpu_percent": 48.2,
    "avg_ram_percent": 52.1,
    "avg_error_rate_percent": 1.4
  },
  "recent_incidents": [ /* Incident objects */ ],
  "open_incidents_count": 4,
  "ai_workflow_status": {
    "last_run_id": "RUN-A1B2C3D4",
    "last_run_status": "success",
    "last_run_at": "2026-07-21T09:12:00Z",
    "total_runs": 6
  },
  "recent_activities": [ /* activity feed items */ ],
  "generated_at": "2026-07-21T09:15:00Z"
}
```

---

## `GET /infrastructure`

Query params: `type` (api|microservice|database|container|cache|queue), `status` (healthy|degraded|critical|offline)

Returns the full service inventory with summary counts. When `LIVE_MONITORING=true`, this
includes a real `host-system` entry populated by psutil, alongside any auto-registered services
discovered from watched application logs.

## `GET /infrastructure/{service_id}`

Returns a single service plus its metrics history (last 24h) and recent logs.

## `GET /infrastructure/{service_id}/logs`

Query params: `level` (INFO|WARN|ERROR|DEBUG), `limit` (default 100)

---

## `GET /incidents`

Query params: `status` (open|investigating|identified|monitoring|resolved), `severity` (critical|high|medium|low)

## `GET /incidents/{incident_id}`

Returns full incident detail including the AI-generated timeline and linked recommendation.

---

## `GET /analytics`

Returns pre-aggregated series for all Analytics page charts: `response_time_trend`,
`cpu_trend`, `ram_trend`, `error_rate_trend`, `incident_trend`, `severity_breakdown`,
`top_failing_services`, `service_availability`.

---

## `POST /analyze`

Request body:

```json
{ "service_id": "payment-gateway-api" }
```

Runs a lightweight on-demand risk assessment against a single service without triggering the
full LangGraph workflow.

---

## `POST /workflow/run`

Request body (optional):

```json
{ "trigger": "manual", "target_service_id": null }
```

Executes the full 8-agent LangGraph pipeline synchronously and returns a `WorkflowRun` object
with per-agent step timings and outcomes. The same pipeline also runs automatically every
`SCHEDULER_INTERVAL_SECONDS` (default 30s) when `LIVE_MONITORING=true`.

## `GET /workflow/nodes`

Returns the static node/edge definition consumed by the React Flow diagram on the Workflow page.

## `GET /workflow/history`

Query params: `limit` (default 20). Returns recent workflow run history.

---

## `GET /metrics`

Returns a fresh real-time system snapshot collected directly via psutil: CPU (overall + per-core),
RAM, disk, network throughput (KB/s), top processes by CPU, and system uptime.

## `GET /metrics/history`

Query params: `limit` (default 100). Returns recent historical system metric snapshots collected
on each Infrastructure Health Agent run.

## `GET /metrics/services/{service_id}`

Query params: `limit` (default 200). Returns time-series metrics for a single service, real or
simulated.

---

## `GET /logs`

Query params: `service_id`, `level` (INFO|WARN|ERROR|DEBUG), `limit` (default 200, max 1000).
Queries across all services, real and simulated — distinct from the per-service
`/infrastructure/{service_id}/logs` endpoint.

---

## `GET /recommendations`

Query params: `limit` (default 50, max 200). Returns the AI recommendation feed, most recent
first, generated dynamically from the actual observed metrics/logs behind each incident.

---

## Guardian Agents (see `/guardian-agent`)

### `GET /agents`

Requires a user JWT (same as every other dashboard endpoint). Returns every Guardian Agent that
has ever sent telemetry, with a computed `online` flag (true if telemetry was received within
`AGENT_OFFLINE_AFTER_SECONDS`, default 90s).

```json
{
  "total": 2,
  "online": 1,
  "agents": [
    {
      "agent_id": "guardian-a1b2c3d4e5f6",
      "hostname": "prod-node-07",
      "os": "Linux-5.15",
      "service_id": "agent-prod-node-07",
      "first_seen": "2026-07-23T09:00:00Z",
      "last_seen": "2026-07-23T10:05:00Z",
      "online": true
    }
  ]
}
```

### `POST /agents/telemetry`

Requires the `X-Agent-Api-Key` header (must match `AGENT_API_KEY`) — **not** a user JWT, since a
Guardian Agent is a standalone process rather than a logged-in operator.

```json
{
  "agent_id": "guardian-a1b2c3d4e5f6",
  "hostname": "prod-node-07",
  "os": "Linux-5.15",
  "metrics": {
    "timestamp": "2026-07-23T10:05:00Z",
    "cpu": { "percent": 42.1 },
    "ram": { "percent": 58.3 },
    "disk": { "percent": 61.0 },
    "network": { "sent_kbps": 12.4, "recv_kbps": 30.8 },
    "uptime": { "uptime_human": "3d 4h 10m" },
    "process_count": 128
  },
  "logs": [
    { "service_id": "payment-service", "line": "2026-07-23 10:04:58 [ERROR] payment-service: Database connection timeout" }
  ]
}
```

Response:

```json
{
  "accepted": true,
  "agent_id": "guardian-a1b2c3d4e5f6",
  "metrics_ingested": true,
  "logs_ingested": 1,
  "server_time": "2026-07-23T10:05:01Z"
}
```

The agent's host is folded into the shared infrastructure schema (visible on the Infrastructure
page like any other service, tagged `agent` + `live`), and any raw log lines are parsed
server-side by the same `log_parser.py` used for locally-watched logs. No further wiring is
needed for this telemetry to reach the LangGraph workflow — the existing 30-second scheduler (or
a manual `POST /workflow/run`) evaluates any `live`-tagged service on its next pass.

---

## `GET /health`

Lightweight health check used by the frontend Topbar's "Backend Live" indicator. Does not
require authentication.

