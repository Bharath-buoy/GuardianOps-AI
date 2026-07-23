import { useState } from "react";
import { ShieldAlert } from "lucide-react";
import { PageContainer, Card, SectionHeading } from "../components/common/Card";
import { PageSkeleton, EmptyState } from "../components/common/Skeleton";
import IncidentCard from "../components/incidents/IncidentCard";
import { usePolling } from "../hooks/usePolling";
import { endpoints } from "../services/api";

const STATUS_TABS = [
  { value: "", label: "All" },
  { value: "open", label: "Open" },
  { value: "investigating", label: "Investigating" },
  { value: "monitoring", label: "Monitoring" },
  { value: "resolved", label: "Resolved" },
];

const SEVERITY_FILTERS = [
  { value: "", label: "All Severities" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

export default function Incidents() {
  const [statusTab, setStatusTab] = useState("");
  const [severity, setSeverity] = useState("");

  const { data, loading } = usePolling(
    () => endpoints.incidents({ status: statusTab || undefined, severity: severity || undefined }).then((r) => r.data),
    { intervalMs: 7000, deps: [statusTab, severity] }
  );

  if (loading && !data) return <PageSkeleton />;

  if (!data) {
    return (
      <PageContainer>
        <Card>
          <EmptyState icon={ShieldAlert} title="Unable to load incidents" description="Check that the backend is running." />
        </Card>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="text-center py-4">
          <p className="text-2xl font-bold text-white">{data.total}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Total Incidents</p>
        </Card>
        <Card className="text-center py-4" delay={0.05}>
          <p className="text-2xl font-bold text-red-400">{data.open}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Open</p>
        </Card>
        <Card className="text-center py-4" delay={0.1}>
          <p className="text-2xl font-bold text-amber-400">{data.investigating}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Investigating</p>
        </Card>
        <Card className="text-center py-4" delay={0.15}>
          <p className="text-2xl font-bold text-emerald-400">{data.resolved}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Resolved</p>
        </Card>
      </div>

      <Card>
        <SectionHeading title="Incident Timeline" subtitle={`${data.incidents.length} incident(s) shown`} />

        <div className="flex flex-wrap items-center gap-2 mb-5">
          <div className="flex gap-1 p-1 rounded-xl bg-white/[0.03] border border-white/5">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setStatusTab(tab.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  statusTab === tab.value ? "bg-cyan-500/15 text-cyan-300" : "text-gray-500 hover:text-gray-300"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="ml-auto px-3 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-gray-300 focus:outline-none focus:border-cyan-500/40"
          >
            {SEVERITY_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>

        {data.incidents.length === 0 ? (
          <EmptyState icon={ShieldAlert} title="No incidents found" description="No incidents match the selected filters." />
        ) : (
          <div className="space-y-3">
            {data.incidents.map((incident, idx) => (
              <IncidentCard key={incident.incident_id} incident={incident} delay={Math.min(idx * 0.03, 0.3)} />
            ))}
          </div>
        )}
      </Card>
    </PageContainer>
  );
}
