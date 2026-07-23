import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Radio, Wifi, WifiOff, LogOut } from "lucide-react";
import { endpoints } from "../../services/api";
import { useAuth } from "../../context/AuthContext";

export default function Topbar({ title, subtitle }) {
  const [online, setOnline] = useState(true);
  const [now, setNow] = useState(new Date());
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const clockTimer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(clockTimer);
  }, []);

  useEffect(() => {
    let mounted = true;
    const checkHealth = async () => {
      try {
        await endpoints.health();
        if (mounted) setOnline(true);
      } catch {
        if (mounted) setOnline(false);
      }
    };
    checkHealth();
    const t = setInterval(checkHealth, 10000);
    return () => {
      mounted = false;
      clearInterval(t);
    };
  }, []);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="sticky top-0 z-30 h-16 flex items-center justify-between px-6 border-b border-white/5 bg-[#0a0e17]/85 backdrop-blur-md">
      <div>
        <h1 className="text-lg font-semibold text-white tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-gray-500">
          {now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
        </div>
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border ${
            online
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
              : "bg-red-500/10 text-red-400 border-red-500/25"
          }`}
        >
          {online ? <Wifi size={12} /> : <WifiOff size={12} />}
          {online ? "Backend Live" : "Backend Offline"}
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
          <Radio size={12} className="animate-pulse-dot" />
          Monitoring
        </div>
        {user && (
          <button
            onClick={handleLogout}
            title={`Signed in as ${user.email}`}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-white/5 text-gray-400 border border-white/10 hover:text-red-400 hover:border-red-500/25 transition"
          >
            <LogOut size={12} />
            Logout
          </button>
        )}
      </div>
    </header>
  );
}
