import { motion } from "framer-motion";
import { Cpu, MemoryStick, Timer, Percent, Database, Server, Box, Layers } from "lucide-react";
import { StatusBadge } from "../common/StatusBadge";
import { formatMs, formatPercent, formatNumber } from "../../utils/format";

const TYPE_ICONS = {
  api: Server,
  microservice: Layers,
  database: Database,
  container: Box,
  cache: Cpu,
  queue: Layers,
};

function MetricBar({ label, value, colorClass }) {
  return (
    <div>
      <div className="flex justify-between text-[11px] text-gray-500 mb-1">
        <span>{label}</span>
        <span className="font-mono text-gray-400">{formatPercent(value)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
        <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    </div>
  );
}

export default function ServiceCard({ service, delay = 0, onClick }) {
  const Icon = TYPE_ICONS[service.type] || Server;
  const cpuColor = service.cpu_percent > 80 ? "bg-red-400" : service.cpu_percent > 60 ? "bg-amber-400" : "bg-cyan-400";
  const ramColor = service.ram_percent > 80 ? "bg-red-400" : service.ram_percent > 60 ? "bg-amber-400" : "bg-violet-400";

  return (
    <motion.button
      onClick={onClick}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      whileHover={{ y: -3 }}
      className="text-left glass-panel rounded-2xl p-4 hover:border-cyan-500/30 transition-colors border border-white/5"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-1.5 rounded-lg bg-white/5 shrink-0">
            <Icon size={15} className="text-gray-400" />
          </div>
          <p className="text-sm font-semibold text-gray-100 truncate">{service.name}</p>
        </div>
        <StatusBadge status={service.status} />
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-2 mb-3 text-xs">
        <div>
          <p className="text-gray-500">Uptime</p>
          <p className="font-mono text-gray-300">{formatPercent(service.uptime_percent, 2)}</p>
        </div>
        <div>
          <p className="text-gray-500">Latency</p>
          <p className="font-mono text-gray-300">{formatMs(service.latency_ms)}</p>
        </div>
        <div>
          <p className="text-gray-500">Req/min</p>
          <p className="font-mono text-gray-300">{formatNumber(service.requests_per_min)}</p>
        </div>
        <div>
          <p className="text-gray-500">Error Rate</p>
          <p className="font-mono text-gray-300">{formatPercent(service.error_rate_percent)}</p>
        </div>
      </div>

      <div className="space-y-2">
        <MetricBar label="CPU" value={service.cpu_percent} colorClass={cpuColor} />
        <MetricBar label="RAM" value={service.ram_percent} colorClass={ramColor} />
      </div>

      <div className="flex flex-wrap gap-1 mt-3">
        {service.tags.slice(0, 3).map((tag) => (
          <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-gray-500">
            {tag}
          </span>
        ))}
      </div>
    </motion.button>
  );
}
