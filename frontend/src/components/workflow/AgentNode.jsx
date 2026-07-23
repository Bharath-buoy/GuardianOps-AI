import { Handle, Position } from "reactflow";
import { Cpu, FileSearch, Gauge, Radar, Siren, Search, Lightbulb, BellRing, Database, LayoutDashboard } from "lucide-react";

const ICONS = {
  "infra-health": Gauge,
  "log-analysis": FileSearch,
  metrics: Cpu,
  "api-monitoring": Radar,
  "incident-detection": Siren,
  "root-cause-analysis": Search,
  recommendation: Lightbulb,
  notification: BellRing,
  mongodb: Database,
  "dashboard-update": LayoutDashboard,
};

export default function AgentNode({ data }) {
  const Icon = ICONS[data.id] || Cpu;
  const isActive = data.status === "running";
  const isDone = data.status === "success";

  const ring =
    isActive
      ? "border-cyan-400 shadow-[0_0_0_3px_rgba(6,182,212,0.25)]"
      : isDone
      ? "border-emerald-500/50"
      : "border-white/10";

  return (
    <div
      className={`glass-panel rounded-2xl px-4 py-3 w-52 border-2 transition-all duration-300 ${ring} ${
        isActive ? "scale-105" : ""
      }`}
    >
      <Handle type="target" position={Position.Left} className="!bg-cyan-500 !w-2 !h-2" />
      <div className="flex items-center gap-2.5">
        <div
          className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
            isActive ? "bg-cyan-500/20 text-cyan-300" : isDone ? "bg-emerald-500/15 text-emerald-400" : "bg-white/5 text-gray-400"
          }`}
        >
          <Icon size={16} className={isActive ? "animate-pulse-dot" : ""} />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-semibold text-gray-100 leading-tight truncate">{data.label}</p>
          <p className="text-[10px] text-gray-500 mt-0.5 capitalize">{data.status || "idle"}</p>
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-cyan-500 !w-2 !h-2" />
    </div>
  );
}
