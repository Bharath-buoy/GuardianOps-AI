import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Area,
  AreaChart,
} from "recharts";

const tooltipStyle = {
  background: "#141a2a",
  border: "1px solid #2d3748",
  borderRadius: 10,
  fontSize: 12,
  color: "#e5e7eb",
};

function formatTick(value) {
  if (!value) return "";
  const d = new Date(value.length <= 13 ? `${value}:00:00` : value);
  return d.toLocaleTimeString([], { hour: "2-digit" });
}

export function TrendAreaChart({ data, dataKey = "value", color = "#06b6d4", xKey = "time", unit = "" }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id={`grad-${dataKey}-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.35} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
        <XAxis
          dataKey={xKey}
          tickFormatter={formatTick}
          stroke="#4b5563"
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis stroke="#4b5563" fontSize={11} tickLine={false} axisLine={false} width={36} />
        <Tooltip
          contentStyle={tooltipStyle}
          labelFormatter={formatTick}
          formatter={(v) => [`${v}${unit}`, ""]}
        />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          fill={`url(#grad-${dataKey}-${color.replace("#", "")})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function MultiLineChart({ data, lines, xKey = "time" }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
        <XAxis dataKey={xKey} tickFormatter={formatTick} stroke="#4b5563" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis stroke="#4b5563" fontSize={11} tickLine={false} axisLine={false} width={36} />
        <Tooltip contentStyle={tooltipStyle} labelFormatter={formatTick} />
        {lines.map((l) => (
          <Line
            key={l.dataKey}
            type="monotone"
            dataKey={l.dataKey}
            name={l.name}
            stroke={l.color}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
