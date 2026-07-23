import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Server,
  AlertTriangle,
  BarChart3,
  GitBranch,
  Info,
  ShieldCheck,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/infrastructure", label: "Infrastructure", icon: Server },
  { to: "/incidents", label: "Incidents", icon: AlertTriangle },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/workflow", label: "Workflow", icon: GitBranch },
  { to: "/about", label: "About", icon: Info },
];

export default function Sidebar() {
  return (
    <aside className="hidden md:flex md:flex-col w-64 shrink-0 h-screen sticky top-0 border-r border-white/5 bg-[#0b0f1a]">
      <div className="flex items-center gap-2.5 px-6 h-16 border-b border-white/5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-violet-500 flex items-center justify-center glow-cyan">
          <ShieldCheck size={18} className="text-[#0a0e17]" strokeWidth={2.5} />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-bold tracking-tight text-white">GuardianOps</p>
          <p className="text-[10px] font-mono uppercase tracking-widest text-cyan-400/80">AI Platform</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? "bg-gradient-to-r from-cyan-500/15 to-violet-500/10 text-cyan-300 border border-cyan-500/20"
                  : "text-gray-400 hover:text-gray-100 hover:bg-white/5 border border-transparent"
              }`
            }
          >
            <Icon size={17} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-white/5">
        <div className="rounded-xl p-3 glass-panel">
          <p className="text-[11px] text-gray-400 leading-relaxed">
            Guardian Agent Connected

            Real-time monitoring
            AI-powered analysis
            Cloud-native deployment
          </p>
        </div>
      </div>
    </aside>
  );
}
