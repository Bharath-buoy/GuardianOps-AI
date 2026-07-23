import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { StatusBadge } from "../common/StatusBadge";
import { TrendAreaChart } from "../dashboard/Charts";
import { formatMs, formatPercent, timeAgo } from "../../utils/format";

export default function ServiceDetailDrawer({ service, metrics, logs, onClose }) {
  return (
    <AnimatePresence>
      {service && (
        <>
          <motion.div
            className="fixed inset-0 bg-black/60 z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            className="fixed right-0 top-0 h-full w-full sm:w-[480px] bg-[#0f1420] border-l border-white/10 z-50 overflow-y-auto"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 260 }}
          >
            <div className="sticky top-0 bg-[#0f1420]/95 backdrop-blur border-b border-white/5 px-5 py-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-white">{service.name}</p>
                <p className="text-xs text-gray-500">{service.type} · {service.region}</p>
              </div>
              <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/5 text-gray-400">
                <X size={18} />
              </button>
            </div>

            <div className="p-5 space-y-5">
              <div className="flex items-center justify-between">
                <StatusBadge status={service.status} />
                <p className="text-xs text-gray-500">v{service.version} · deployed {timeAgo(service.last_deployed)}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {[
                  ["Uptime", formatPercent(service.uptime_percent, 2)],
                  ["Latency", formatMs(service.latency_ms)],
                  ["CPU", formatPercent(service.cpu_percent)],
                  ["RAM", formatPercent(service.ram_percent)],
                  ["Error Rate", formatPercent(service.error_rate_percent)],
                  ["Req/min", service.requests_per_min],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-xl bg-white/[0.03] border border-white/5 p-3">
                    <p className="text-[11px] text-gray-500">{label}</p>
                    <p className="text-sm font-mono text-gray-200 mt-1">{value}</p>
                  </div>
                ))}
              </div>

              {metrics && metrics.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Latency Trend</p>
                  <TrendAreaChart data={metrics} dataKey="latency_ms" xKey="timestamp" color="#06b6d4" unit="ms" />
                </div>
              )}

              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Recent Logs</p>
                <div className="space-y-1.5 max-h-64 overflow-y-auto font-mono text-[11px]">
                  {(logs || []).slice(0, 30).map((log) => (
                    <div key={log.log_id} className="flex gap-2 py-1 border-b border-white/5">
                      <span
                        className={`shrink-0 ${
                          log.level === "ERROR"
                            ? "text-red-400"
                            : log.level === "WARN"
                            ? "text-amber-400"
                            : "text-gray-500"
                        }`}
                      >
                        [{log.level}]
                      </span>
                      <span className="text-gray-400 truncate">{log.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
