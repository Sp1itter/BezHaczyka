import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, AreaChart, Area } from "recharts";
import { RISK, RISK_COLOR } from "../../lib/labels.js";

const LEVELS = ["high", "medium", "low"];

// data: [{ date, high, medium, low }]. variant: "bar" (histogram jak Discover) | "area"
export default function TrendChart({ data, height = 220, variant = "area" }) {
  const Chart = variant === "bar" ? BarChart : AreaChart;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <Chart data={data} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "var(--muted)" }} tickFormatter={(d) => d.slice(5)} />
        <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--muted)" }} />
        <Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--border)" }} />
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
