import { motion } from "framer-motion";

export function HealthScoreGauge({ score = 0 }) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 85 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center justify-center py-2">
      <div className="relative w-44 h-44">
        <svg width="176" height="176" viewBox="0 0 176 176" className="-rotate-90">
          <circle cx="88" cy="88" r={radius} fill="none" stroke="#1f2937" strokeWidth="12" />
          <motion.circle
            cx="88"
            cy="88"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold font-mono text-white">{score}</span>
          <span className="text-[11px] text-gray-500 uppercase tracking-wide mt-1">Health Score</span>
        </div>
      </div>
    </div>
  );
}
