import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, AreaChart, Area } from "recharts";
import { RISK, RISK_COLOR } from "../../lib/labels.js";

const LEVELS = ["high", "medium", "low"];
// "2026-11-22" -> "11-22"; "2026-11-22T05" / "2026-11-22T05:40" (kubelki UTC) -> "06:00" / "06:40" (czas lokalny)
const fmtBucket = (d) => (d.length > 10 ? new Date(d.length > 13 ? `${d}:00Z` : `${d}:00:00Z`).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" }) : d.slice(5));

// data: [{ date, high, medium, low }]. variant: "bar" (histogram jak Discover) | "area"
export default function TrendChart({ data, height = 220, variant = "area" }) {
  const Chart = variant === "bar" ? BarChart : AreaChart;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <Chart data={data} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "var(--muted)" }} tickFormatter={fmtBucket} />
        <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--muted)" }} />
        <Tooltip labelFormatter={fmtBucket} contentStyle={{ background: "var(--panel)", border: "1px solid var(--border)" }} />
        <Legend formatter={(v) => RISK[v]} wrapperStyle={{ fontSize: 12 }} />
        {LEVELS.map((l) =>
          variant === "bar" ? (
            <Bar key={l} dataKey={l} stackId="r" fill={RISK_COLOR[l]} />
          ) : (
            <Area key={l} dataKey={l} stackId="r" type="monotone" stroke={RISK_COLOR[l]} fill={RISK_COLOR[l]} fillOpacity={0.35} />
          ),
        )}
      </Chart>
    </ResponsiveContainer>
  );
}
