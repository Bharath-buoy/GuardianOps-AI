import { motion } from "framer-motion";

export function KpiCard({ icon: Icon, label, value, unit, trend, accent = "cyan", delay = 0 }) {
  const accents = {
    cyan: "from-cyan-500/20 to-cyan-500/5 text-cyan-400",
    violet: "from-violet-500/20 to-violet-500/5 text-violet-400",
    emerald: "from-emerald-500/20 to-emerald-500/5 text-emerald-400",
    amber: "from-amber-500/20 to-amber-500/5 text-amber-400",
    red: "from-red-500/20 to-red-500/5 text-red-400",
  };
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
      className="glass-panel rounded-2xl p-5 relative overflow-hidden group"
    >
      <div
        className={`absolute -top-6 -right-6 w-24 h-24 rounded-full bg-gradient-to-br ${accents[accent]} opacity-40 blur-2xl group-hover:opacity-70 transition-opacity`}
      />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</p>
          <p className="mt-2 text-2xl font-bold text-white font-mono">
            {value}
            {unit && <span className="text-sm text-gray-500 ml-1 font-sans">{unit}</span>}
          </p>
          {trend && <p className="mt-1 text-[11px] text-gray-500">{trend}</p>}
        </div>
        {Icon && (
          <div className={`p-2 rounded-xl bg-white/5 ${accents[accent].split(" ").pop()}`}>
            <Icon size={18} strokeWidth={2} />
          </div>
        )}
      </div>
    </motion.div>
  );
}
