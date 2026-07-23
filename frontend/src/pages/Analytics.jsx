import { BarChart3 } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { PageContainer, Card, SectionHeading } from "../components/common/Card";
import { PageSkeleton, EmptyState } from "../components/common/Skeleton";
import { TrendAreaChart, MultiLineChart } from "../components/dashboard/Charts";
import { usePolling } from "../hooks/usePolling";
import { endpoints } from "../services/api";
import { formatPercent, formatMs } from "../utils/format";

const SEVERITY_COLORS_HEX = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#f59e0b",
  low: "#3b82f6",
};

const tooltipStyle = {
  background: "#141a2a",
  border: "1px solid #2d3748",
  borderRadius: 10,
  fontSize: 12,
  color: "#e5e7eb",
};

export default function Analytics() {
  const { data, loading } = usePolling(() => endpoints.analytics().then((r) => r.data), { intervalMs: 10000 });

  if (loading && !data) return <PageSkeleton />;

  if (!data) {
    return (
      <PageContainer>
        <Card>
          <EmptyState icon={BarChart3} title="Unable to load analytics" description="Check that the backend is running." />
        </Card>
      </PageContainer>
    );
  }

  const severityData = Object.entries(data.severity_breakdown).map(([name, value]) => ({ name, value }));

  return (
    <PageContainer>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <SectionHeading title="Response Time Trend" subtitle="Average latency (ms), hourly" />
          <TrendAreaChart data={data.response_time_trend} dataKey="value" xKey="time" color="#06b6d4" unit="ms" />
        </Card>
        <Card delay={0.05}>
          <SectionHeading title="Error Rate Trend" subtitle="Average error rate (%), hourly" />
          <TrendAreaChart data={data.error_rate_trend} dataKey="value" xKey="time" color="#ef4444" unit="%" />
        </Card>
      </div>

      <Card delay={0.1}>
        <SectionHeading title="CPU & RAM Utilization" subtitle="Fleet-wide average, hourly" />
        <MultiLineChart
          xKey="time"
          data={data.cpu_trend.map((c, idx) => ({
            time: c.time,
            cpu: c.value,
            ram: data.ram_trend[idx]?.value ?? null,
          }))}
          lines={[
            { dataKey: "cpu", name: "CPU %", color: "#06b6d4" },
            { dataKey: "ram", name: "RAM %", color: "#8b5cf6" },
          ]}
        />
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-1" delay={0.15}>
          <SectionHeading title="Incidents by Severity" />
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={severityData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={80} paddingAngle={3}>
                {severityData.map((entry) => (
                  <Cell key={entry.name} fill={SEVERITY_COLORS_HEX[entry.name] || "#64748b"} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend
                formatter={(value) => <span className="text-xs text-gray-400 capitalize">{value}</span>}
                iconSize={8}
              />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card className="lg:col-span-2" delay={0.2}>
          <SectionHeading title="Top Failing Services" subtitle="Ranked by error rate & uptime" />
          <div className="space-y-3">
            {data.top_failing_services.map((s) => (
              <div key={s.service_id} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/5">
                <p className="text-sm text-gray-200 font-medium truncate">{s.service_id}</p>
                <div className="flex gap-5 text-xs">
                  <div className="text-right">
                    <p className="text-gray-500">Error Rate</p>
                    <p className="font-mono text-red-400">{formatPercent(s.error_rate_percent)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-500">Uptime</p>
                    <p className="font-mono text-gray-300">{formatPercent(s.uptime_percent, 2)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-500">Latency</p>
                    <p className="font-mono text-gray-300">{formatMs(s.latency_ms)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card delay={0.25}>
        <SectionHeading title="Incident Trend" subtitle="New incidents per day (last 14 days)" />
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data.incident_trend} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
            <XAxis dataKey="date" stroke="#4b5563" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="#4b5563" fontSize={11} tickLine={false} axisLine={false} width={30} allowDecimals={false} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="count" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card delay={0.3}>
        <SectionHeading title="Service Availability" subtitle="Lowest uptime services" />
        <div className="space-y-3">
          {data.service_availability.map((s) => (
            <div key={s.service_id} className="flex items-center gap-3">
              <p className="text-xs text-gray-400 w-48 truncate">{s.service_id}</p>
              <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${s.uptime_percent > 99 ? "bg-emerald-400" : s.uptime_percent > 97 ? "bg-amber-400" : "bg-red-400"}`}
                  style={{ width: `${s.uptime_percent}%` }}
                />
              </div>
              <p className="text-xs font-mono text-gray-400 w-16 text-right">{formatPercent(s.uptime_percent, 2)}</p>
            </div>
          ))}
        </div>
      </Card>
    </PageContainer>
  );
}
