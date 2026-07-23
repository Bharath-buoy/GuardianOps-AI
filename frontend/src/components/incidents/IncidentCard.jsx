import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Clock, Target, Lightbulb, ListTree } from "lucide-react";
import { useState } from "react";
import { SeverityBadge } from "../common/StatusBadge";
import { timeAgo, formatClockTime } from "../../utils/format";

export default function IncidentCard({ incident, delay = 0 }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="glass-panel rounded-2xl overflow-hidden border border-white/5"
    >
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between gap-4 p-4 text-left hover:bg-white/[0.02] transition"
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-mono text-gray-500">{incident.incident_id}</span>
            <SeverityBadge severity={incident.severity} />
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-white/5 text-gray-400 capitalize">
              {incident.status}
            </span>
          </div>
          <p className="text-sm font-semibold text-gray-100 mt-1.5 truncate">{incident.title}</p>
          <p className="text-xs text-gray-500 mt-1">
            {timeAgo(incident.created_at)} · Affects: {incident.affected_services.join(", ")}
          </p>
        </div>
        <ChevronDown size={18} className={`shrink-0 text-gray-500 transition-transform ${expanded ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden border-t border-white/5"
          >
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="rounded-xl bg-white/[0.03] border border-white/5 p-3">
                  <div className="flex items-center gap-1.5 text-cyan-400 mb-1.5">
                    <Target size={13} />
                    <p className="text-[11px] font-semibold uppercase tracking-wide">AI Summary</p>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">{incident.ai_summary}</p>
                </div>
                <div className="rounded-xl bg-white/[0.03] border border-white/5 p-3">
                  <div className="flex items-center gap-1.5 text-violet-400 mb-1.5">
                    <ListTree size={13} />
                    <p className="text-[11px] font-semibold uppercase tracking-wide">Root Cause</p>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">{incident.root_cause}</p>
                </div>
                <div className="rounded-xl bg-white/[0.03] border border-white/5 p-3">
                  <div className="flex items-center gap-1.5 text-emerald-400 mb-1.5">
                    <Lightbulb size={13} />
                    <p className="text-[11px] font-semibold uppercase tracking-wide">Recommendation</p>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">{incident.recommendation}</p>
                </div>
              </div>

              <div>
                <div className="flex items-center gap-1.5 text-gray-400 mb-3">
                  <Clock size={13} />
                  <p className="text-[11px] font-semibold uppercase tracking-wide">Timeline</p>
                </div>
                <div className="space-y-0">
                  {incident.timeline.map((event, idx) => (
                    <div key={idx} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <span className="w-2 h-2 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                        {idx < incident.timeline.length - 1 && <span className="w-px flex-1 bg-white/10" />}
                      </div>
                      <div className="pb-4 min-w-0">
                        <p className="text-xs font-medium text-gray-200">
                          {event.label}{" "}
                          <span className="text-gray-600 font-normal">· {formatClockTime(event.timestamp)}</span>
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">{event.description}</p>
                        <p className="text-[10px] text-gray-600 mt-0.5">{event.actor}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-gray-500 pt-1 border-t border-white/5">
                <span>Confidence score: <span className="text-cyan-400 font-mono">{Math.round(incident.confidence_score * 100)}%</span></span>
                <span>Detected by {incident.detected_by}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
