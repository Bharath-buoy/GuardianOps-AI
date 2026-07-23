export function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatPercent(value, decimals = 1) {
  if (value === null || value === undefined) return "—";
  return `${Number(value).toFixed(decimals)}%`;
}

export function formatMs(value) {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value)}ms`;
}

export function timeAgo(isoString) {
  if (!isoString) return "—";
  const date = new Date(isoString);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function formatClockTime(isoString) {
  if (!isoString) return "—";
  const date = new Date(isoString);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export const STATUS_COLORS = {
  healthy: { text: "text-emerald-400", bg: "bg-emerald-500/15", dot: "bg-emerald-400", border: "border-emerald-500/30" },
  degraded: { text: "text-amber-400", bg: "bg-amber-500/15", dot: "bg-amber-400", border: "border-amber-500/30" },
  critical: { text: "text-red-400", bg: "bg-red-500/15", dot: "bg-red-400", border: "border-red-500/30" },
  offline: { text: "text-gray-400", bg: "bg-gray-500/15", dot: "bg-gray-400", border: "border-gray-500/30" },
};

export const SEVERITY_COLORS = {
  critical: { text: "text-red-400", bg: "bg-red-500/15", border: "border-red-500/30" },
  high: { text: "text-orange-400", bg: "bg-orange-500/15", border: "border-orange-500/30" },
  medium: { text: "text-amber-400", bg: "bg-amber-500/15", border: "border-amber-500/30" },
  low: { text: "text-blue-400", bg: "bg-blue-500/15", border: "border-blue-500/30" },
};
