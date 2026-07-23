import { useState } from "react";
import { Search, Server } from "lucide-react";
import { PageContainer, Card, SectionHeading } from "../components/common/Card";
import { PageSkeleton, EmptyState } from "../components/common/Skeleton";
import ServiceCard from "../components/infrastructure/ServiceCard";
import ServiceDetailDrawer from "../components/infrastructure/ServiceDetailDrawer";
import { usePolling } from "../hooks/usePolling";
import { endpoints } from "../services/api";

const TYPE_FILTERS = [
  { value: "", label: "All Types" },
  { value: "api", label: "APIs" },
  { value: "microservice", label: "Microservices" },
  { value: "database", label: "Databases" },
  { value: "container", label: "Containers" },
  { value: "cache", label: "Cache" },
  { value: "queue", label: "Queues" },
];

const STATUS_FILTERS = [
  { value: "", label: "All Status" },
  { value: "healthy", label: "Healthy" },
  { value: "degraded", label: "Degraded" },
  { value: "critical", label: "Critical" },
  { value: "offline", label: "Offline" },
];

export default function Infrastructure() {
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);

  const { data, loading } = usePolling(() => endpoints.infrastructure().then((r) => r.data), {
    intervalMs: 6000,
  });

  async function openService(service) {
    setSelected(service);
    try {
      const res = await endpoints.serviceDetail(service.service_id);
      setDetail(res.data);
    } catch {
      setDetail(null);
    }
  }

  if (loading && !data) return <PageSkeleton />;

  if (!data) {
    return (
      <PageContainer>
        <Card>
          <EmptyState icon={Server} title="Unable to load infrastructure" description="Check that the backend is running." />
        </Card>
      </PageContainer>
    );
  }

  const filtered = data.services.filter((s) => {
    if (typeFilter && s.type !== typeFilter) return false;
    if (statusFilter && s.status !== statusFilter) return false;
    if (search && !s.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <PageContainer>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="text-center py-4">
          <p className="text-2xl font-bold text-white">{data.total}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Total Services</p>
        </Card>
        <Card className="text-center py-4" delay={0.05}>
          <p className="text-2xl font-bold text-emerald-400">{data.healthy}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Healthy</p>
        </Card>
        <Card className="text-center py-4" delay={0.1}>
          <p className="text-2xl font-bold text-amber-400">{data.degraded}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Degraded</p>
        </Card>
        <Card className="text-center py-4" delay={0.15}>
          <p className="text-2xl font-bold text-red-400">{data.critical}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Critical</p>
        </Card>
      </div>

      <Card>
        <SectionHeading title="Service Inventory" subtitle={`${filtered.length} of ${data.total} services shown`} />
        <div className="flex flex-col sm:flex-row gap-3 mb-5">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search services..."
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/40"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-gray-300 focus:outline-none focus:border-cyan-500/40"
          >
            {TYPE_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-gray-300 focus:outline-none focus:border-cyan-500/40"
          >
            {STATUS_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>

        {filtered.length === 0 ? (
          <EmptyState icon={Search} title="No services match your filters" description="Try adjusting your search or filters." />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {filtered.map((service, idx) => (
              <ServiceCard
                key={service.service_id}
                service={service}
                delay={Math.min(idx * 0.03, 0.3)}
                onClick={() => openService(service)}
              />
            ))}
          </div>
        )}
      </Card>

      <ServiceDetailDrawer
        service={selected}
        metrics={detail?.metrics_history}
        logs={detail?.recent_logs}
        onClose={() => {
          setSelected(null);
          setDetail(null);
        }}
      />
    </PageContainer>
  );
}
