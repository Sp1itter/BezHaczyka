// Pas trendu (120 px): wyniki na dzien wg poziomu ryzyka, z /stats/trend z tymi samymi filtrami co tabela.
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Text } from "@mantine/core";
import { RISK_LABEL, TOKENS } from "../theme.js";

const LEVELS = ["high", "medium", "low"];

export default function TrendStrip({ items }) {
  if (!items?.length) return <Text size="sm" c="dimmed" py="md">Brak wyników w wybranym zakresie dat.</Text>;
  return (
    <ResponsiveContainer width="100%" height={120}>
      <BarChart data={items} margin={{ top: 6, right: 8, left: -24, bottom: 0 }} barCategoryGap={2} maxBarSize={28}>
        <CartesianGrid vertical={false} stroke={TOKENS.border} />
        <XAxis dataKey="date" tickFormatter={(d) => d.slice(8, 10) + "." + d.slice(5, 7)} tick={{ fontSize: 11, fill: TOKENS.muted }}
          axisLine={{ stroke: TOKENS.border }} tickLine={false} />
        <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: TOKENS.muted }} axisLine={false} tickLine={false} width={48} />
        <Tooltip formatter={(v, k) => [v, RISK_LABEL[k] || k]} labelFormatter={(d) => `Dzień ${d}`}
          contentStyle={{ fontSize: 12, border: `1px solid ${TOKENS.border}`, borderRadius: 4 }} />
        {LEVELS.map((l) => <Bar key={l} dataKey={l} stackId="r" fill={TOKENS.risk[l]} isAnimationActive={false} />)}
      </BarChart>
    </ResponsiveContainer>
  );
}
