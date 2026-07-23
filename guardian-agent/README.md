# 🛡️ Guardian Agent

A lightweight, standalone telemetry agent for **GuardianOps AI**. Install it on any machine —
your laptop, a VM, a production server — and it reports real system health and application logs
back to your GuardianOps AI dashboard, where the existing LangGraph AI pipeline picks it up
automatically.

The agent is intentionally tiny: three Python files, three dependencies (`psutil`, `watchdog`,
`requests`), no database, no framework. It collects, buffers, and POSTs — the GuardianOps AI
backend does all the parsing and AI reasoning.

---

## What it does, every 30 seconds

1. Collects real host metrics via **psutil**: CPU usage, RAM usage, disk usage, network
   throughput, running processes, and system uptime.
2. Tails any new lines appended to watched log files via **watchdog** (no polling, no manual
   upload — it reacts to file changes as they happen).
3. Sends both as a single JSON telemetry batch to your GuardianOps AI backend's
   `POST /api/agents/telemetry` endpoint, authenticated with an API key.
4. GuardianOps AI folds this straight into its existing infrastructure schema — your host shows
   up in the Infrastructure page like any other service, and the same LangGraph multi-agent
   workflow (Infrastructure Health → Log Analysis → Metrics → API Monitoring → Incident
   Detection → Root Cause Analysis → Recommendation → Notification) evaluates it on its next run,
   exactly like every other monitored service.

No changes to the GuardianOps AI dashboard are needed — telemetry from connected agents appears
automatically.

---

## Requirements

- Python 3.9+
- Network access from the agent's machine to your GuardianOps AI backend (default port `8000`)

---

## Installation (on the machine you want to monitor)

### 1. Copy this folder

Copy the entire `guardian-agent/` folder to the target machine (via `git clone`, `scp`, a zip
download — whatever's convenient). It doesn't need to sit next to the GuardianOps AI backend or
frontend; it's fully standalone.

### 2. Install dependencies

```bash
cd guardian-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure the agent

Open `config.json` and set:

```json
{
  "server_url": "http://YOUR-GUARDIANOPS-SERVER:8000",
  "api_key": "match-the-AGENT_API_KEY-on-your-backend",
  "agent_id": "",
  "logs_dir": "./logs",
  "send_interval_seconds": 30,
  "request_timeout_seconds": 10
}
```

| Field | Description |
|---|---|
| `server_url` | Base URL of your GuardianOps AI **backend** (not the frontend) — e.g. `http://192.168.1.50:8000` or your deployed Render URL |
| `api_key` | Must exactly match `AGENT_API_KEY` in the GuardianOps AI backend's `.env` file |
| `agent_id` | Leave blank — the agent generates and saves a stable ID here on first run |
| `logs_dir` | Local directory to watch for application log files (see supported filenames below) |
| `send_interval_seconds` | How often to send telemetry (default: 30s, matching the backend's own scheduler cadence) |

### 4. Point `logs_dir` at your application's logs

The agent watches `logs_dir` (recursively) for:

- `application.log`
- `app.log`
- `server.log`
- any other `*.log` or `*.jsonl` file

For the generic names above, the **parent folder name** becomes the service name shown in
GuardianOps AI (e.g. `logs/payment-service/app.log` → service `payment-service`). Any other
filename uses its own stem (e.g. `logs/inventory-service.log` → service `inventory-service`).

If your application already logs to a different location, either point `logs_dir` at that folder
directly, or symlink/copy the log files under `guardian-agent/logs/`.

### 5. Run it

```bash
python agent.py
```

You should see:

```
🛡️  GuardianOps AI Guardian Agent starting
    agent_id : guardian-a1b2c3d4e5f6
    hostname : my-server-01
    os       : Linux-5.15
    server   : http://192.168.1.50:8000
    logs_dir : ./logs
    interval : 30s
👀 Watching ./logs for application.log / app.log / server.log / *.log / *.jsonl
✅ Telemetry sent — metrics_ingested=True, logs_ingested=0
```

Leave it running (use `nohup`, a `systemd` service, `pm2`, Docker, or a Windows service wrapper
to keep it alive in the background — see below).

---

## Connecting to GuardianOps AI

On the **backend**, set `AGENT_API_KEY` in `backend/.env` to a long random string, then restart
the backend:

```bash
# backend/.env
AGENT_API_KEY=some-long-random-shared-secret
AGENT_OFFLINE_AFTER_SECONDS=90
```

Use the **same value** for `api_key` in the agent's `config.json`. That's the entire connection
step — there's no separate registration flow. The first telemetry POST the agent makes registers
it automatically in GuardianOps AI's agent registry (`GET /api/agents`, protected by your normal
operator login) with its agent ID, hostname, OS, and last-seen timestamp.

Once connected, the agent's host appears in the GuardianOps AI **Infrastructure** page as a
regular service (named `agent-<hostname>`), its logs appear in **Incidents**/log views, and any
detected issues (high CPU, high RAM, database timeouts, frequent exceptions, etc.) surface as
real incidents with AI-generated root cause analysis and recommendations — same as everything
else on the dashboard.

---

## Running multiple agents

Every machine you install the Guardian Agent on registers as its own independent agent — just
repeat the install steps above on each machine, using the same `api_key` but letting each one
generate its own `agent_id`. GuardianOps AI's dashboard and `GET /api/agents` list every
connected agent with a live/offline status (offline if no telemetry received in
`AGENT_OFFLINE_AFTER_SECONDS`, default 90s).

---

## Running as a background service

**Linux (systemd)** — create `/etc/systemd/system/guardian-agent.service`:

```ini
[Unit]
Description=GuardianOps AI Guardian Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/guardian-agent
ExecStart=/path/to/guardian-agent/venv/bin/python agent.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now guardian-agent
```

**macOS/Linux (simple background process):**

```bash
nohup python agent.py > agent.log 2>&1 &
```

**Windows:** wrap `agent.py` with [NSSM](https://nssm.cc/) or Task Scheduler set to run at
startup.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `❌ Rejected (401)` | `api_key` in `config.json` doesn't match `AGENT_API_KEY` on the backend |
| `❌ Rejected (503)` | Backend has no `AGENT_API_KEY` set — telemetry ingestion is disabled server-side |
| `Failed to reach GuardianOps AI at ...` | Check `server_url`, firewall rules, and that the backend is running and reachable from this machine |
| Agent's host doesn't appear on the Infrastructure page | Confirm at least one successful `✅ Telemetry sent` log line, then check the backend logs for `📡 Telemetry received from Guardian Agent ...` |
| Logs aren't showing up | Confirm `logs_dir` points at real, actively-written files matching the supported filename patterns above |

---

## Folder contents

```
guardian-agent/
├── agent.py            # Main entrypoint — config loading + send loop
├── collector.py         # psutil metrics collection
├── watcher.py            # watchdog-based log file tailing
├── requirements.txt
├── config.json
├── logs/                # Default watched directory (point elsewhere if you prefer)
└── README.md
```
