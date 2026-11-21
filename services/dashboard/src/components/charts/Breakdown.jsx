import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";

// Poziomy wykres slupkowy. data: { klucz: liczba }, labels: { klucz: etykieta }, colors?: { klucz: kolor }
export default function Breakdown({ data = {}, labels = {}, colors = {}, height = 180 }) {
  const rows = Object.entries(data).map(([k, v]) => ({ key: k, name: labels[k] || k, value: v }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 12, fill: "var(--text)" }} />
        <Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--border)" }} />
        <Bar dataKey="value" radius={[0, 3, 3, 0]} label={{ position: "right", fill: "var(--muted)", fontSize: 11 }}>
          {rows.map((r) => <Cell key={r.key} fill={colors[r.key] || "var(--accent)"} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
