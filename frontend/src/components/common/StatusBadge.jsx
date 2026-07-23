import { STATUS_COLORS, SEVERITY_COLORS } from "../../utils/format";

export function StatusBadge({ status }) {
  const c = STATUS_COLORS[status] || STATUS_COLORS.offline;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${c.bg} ${c.text} ${c.border}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {status?.charAt(0).toUpperCase() + status?.slice(1)}
    </span>
  );
}

export function SeverityBadge({ severity }) {
  const c = SEVERITY_COLORS[severity] || SEVERITY_COLORS.low;
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wide border ${c.bg} ${c.text} ${c.border}`}
    >
      {severity}
    </span>
  );
}
