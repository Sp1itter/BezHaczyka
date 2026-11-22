// Podzial liczby wynikow (np. wg zrodla, modulu, poziomu ryzyka) jako poziome slupki.
// Klikniecie slupka prowadzi do listy wynikow z tym filtrem (jesli podano `hrefFor`).
import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

/**
 * rows: [{ key, label, value, color? }] - kolejnosc jak w tablicy.
 * hrefFor(key) -> adres hash (np. "#/findings?source=tiktok"); bez niego slupki nie sa linkami.
 */
export default function Breakdown({ rows, hrefFor, color = "#6092c0", height }) {
  const h = height || Math.max(90, rows.length * 34 + 10);
  const go = (d) => { if (hrefFor && d?.key != null) window.location.hash = hrefFor(d.key).replace(/^#/, ""); };
  return (
    <ResponsiveContainer width="100%" height={h}>
      <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 40, left: 8, bottom: 4 }}>
        <XAxis type="number" hide allowDecimals={false} />
        <YAxis type="category" dataKey="label" width={150} tick={{ fontSize: 12, fill: "var(--text)" }} axisLine={false} tickLine={false} />
        <Tooltip cursor={{ fill: "var(--grid)" }} contentStyle={{ background: "var(--panel)", border: "1px solid var(--border)" }}
          formatter={(v) => [v, "wyników"]} />
        <Bar dataKey="value" radius={[0, 3, 3, 0]} onClick={go} style={{ cursor: hrefFor ? "pointer" : "default" }}>
          {rows.map((r) => <Cell key={r.key} fill={r.color || color} />)}
          <LabelList dataKey="value" position="right" style={{ fontSize: 12, fill: "var(--muted)" }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
