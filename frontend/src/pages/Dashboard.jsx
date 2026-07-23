import { useState } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import {
  Activity,
  AlertOctagon,
  Cpu,
  MemoryStick,
  Timer,
  TriangleAlert,
  Zap,
  PlayCircle,
  RefreshCcw,
  ListChecks,
} from "lucide-react";
import { PageContainer, Card, SectionHeading } from "../components/common/Card";
import { PageSkeleton, EmptyState } from "../components/common/Skeleton";
import { KpiCard } from "../components/dashboard/KpiCard";
import { HealthScoreGauge } from "../components/dashboard/HealthScoreGauge";
import { SeverityBadge } from "../components/common/StatusBadge";
import { usePolling } from "../hooks/usePolling";
import { endpoints } from "../services/api";
import { timeAgo, formatMs, formatPercent, formatNumber } from "../utils/format";

export default function Dashboard() {
  const { data, loading, refetch } = usePolling(() => endpoints.dashboard().then((r) => r.data), {
    intervalMs: 8000,
  });
  const [running, setRunning] = useState(false);

  async function handleRunWorkflow() {
    setRunning(true);
    const p = endpoints.runWorkflow({ trigger: "manual" });
    toast.promise(p, {
      loading: "Running GuardianOps AI multi-agent workflow…",
      success: (res) =>
        `Workflow complete — ${res.data.incidents_detected} incident(s) detected across ${res.data.steps.length} agents.`,
      error: "Workflow run failed. Check backend connection.",
    });
    try {
      await p;
      refetch();
    } finally {
      setRunning(false);
    }
  }

  if (loading && !data) return <PageSkeleton />;

  if (!data) {
    return (
      <PageContainer>
        <Card>
          <EmptyState
            icon={AlertOctagon}
            title="Unable to reach GuardianOps AI backend"
            description="Make sure the FastAPI server is running at http://localhost:8000 (uvicorn app.main:app --reload)."
          />
        </Card>
      </PageContainer>
    );
  }

  const { health_score, service_counts, kpis, recent_incidents, ai_workflow_status, recent_activities } = data;

  return (
    <PageContainer>
      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon={Activity} label="Healthy Services" value={service_counts.healthy} unit={`/ ${service_counts.total}`} accent="emerald" delay={0.0} />
        <KpiCard icon={TriangleAlert} label="Critical Services" value={service_counts.critical} accent="red" delay={0.05} />
        <KpiCard icon={Timer} label="Avg Response Time" value={formatMs(kpis.avg_response_time_ms)} accent="cyan" delay={0.1} />
        <KpiCard icon={Zap} label="Error Rate" value={formatPercent(kpis.avg_error_rate_percent)} accent="amber" delay={0.15} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Health score */}
        <Card delay={0.1} className="lg:col-span-1 flex flex-col items-center justify-center">
          <SectionHeading title="Infrastructure Health" />
          <HealthScoreGauge score={health_score} />
          <div className="grid grid-cols-2 gap-3 w-full mt-4 text-center">
            <div>
              <p className="text-xs text-gray-500">CPU Usage</p>
              <p className="text-lg font-mono font-semibold text-cyan-400">{formatPercent(kpis.avg_cpu_percent)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">RAM Usage</p>
              <p className="text-lg font-mono font-semibold text-violet-400">{formatPercent(kpis.avg_ram_percent)}</p>
            </div>
          </div>
        </Card>

        {/* Quick actions + workflow status */}
        <Card delay={0.15} className="lg:col-span-2 flex flex-col">
          <SectionHeading title="AI Workflow Status" subtitle="LangGraph multi-agent orchestration" />
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <p className="text-xs text-gray-500">Last run</p>
              <p className="text-sm font-mono text-white">{ai_workflow_status.last_run_id || "No runs yet"}</p>
              <p className="text-xs text-gray-500 mt-1">
                {ai_workflow_status.last_run_at ? timeAgo(ai_workflow_status.last_run_at) : "—"} ·{" "}
                {formatNumber(ai_workflow_status.total_runs)} total runs
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleRunWorkflow}
                disabled={running}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-500 text-[#0a0e17] text-sm font-semibold hover:opacity-90 transition disabled:opacity-50"
              >
                <PlayCircle size={16} />
                {running ? "Running…" : "Run Workflow"}
              </button>
              <button
                onClick={refetch}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 text-gray-300 text-sm hover:bg-white/10 transition"
              >
                <RefreshCcw size={15} />
              </button>
            </div>
          </div>

          <div className="mt-5 grid grid-cols-3 gap-3">
            {["Infrastructure Health", "Incident Detection", "Recommendation"].map((label, idx) => (
              <motion.div
                key={label}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 + idx * 0.1 }}
                className="rounded-xl bg-white/[0.03] border border-white/5 p-3"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-dot" />
                  <p className="text-[11px] text-gray-400">{label} Agent</p>
                </div>
                <p className="text-xs text-gray-600">Idle — ready</p>
              </motion.div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent Incidents */}
        <Card delay={0.2}>
          <SectionHeading title="Recent Incidents" subtitle={`${recent_incidents.length} shown`} />
          {recent_incidents.length === 0 ? (
            <EmptyState icon={ListChecks} title="No incidents detected" description="All systems operating normally." />
          ) : (
            <div className="space-y-3">
              {recent_incidents.map((inc) => (
                <div key={inc.incident_id} className="flex items-start justify-between gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/5">
                  <div className="min-w-0">
                    <p className="text-sm text-gray-200 font-medium truncate">{inc.title}</p>
                    <p className="text-xs text-gray-500 mt-1">{timeAgo(inc.created_at)} · {inc.affected_services.join(", ")}</p>
                  </div>
                  <SeverityBadge severity={inc.severity} />
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Recent Activities */}
        <Card delay={0.25}>
          <SectionHeading title="Recent Activity" />
          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
            {recent_activities.map((a, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <span
                  className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${
                    a.type === "workflow" ? "bg-violet-400" : a.severity === "critical" ? "bg-red-400" : "bg-cyan-400"
                  }`}
                />
                <div className="min-w-0">
                  <p className="text-xs text-gray-300 truncate">{a.message}</p>
                  <p className="text-[11px] text-gray-600">{timeAgo(a.timestamp)}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </PageContainer>
  );
}
