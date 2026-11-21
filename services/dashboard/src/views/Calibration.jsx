import { useMemo, useState } from "react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ReferenceLine } from "recharts";
import Panel from "../components/common/Panel.jsx";
import StatTile from "../components/common/StatTile.jsx";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { confusion, sweep } from "../lib/calibration.js";

// Panel kalibracji: prog score -> FP vs FN, precyzja i pelnosc. Liczone w przegladarce.
export default function Calibration({ threshold, onThreshold }) {
  const gold = useApi(() => api.calibration(), []);
  const items = gold.data?.items || [];
  const cm = useMemo(() => confusion(items, threshold), [items, threshold]);
  const curve = useMemo(() => sweep(items), [items]);
  const pct = (x) => `${Math.round(x * 100)}%`;
  return (
    <div className="grid">
      <Panel title="Próg ryzyka (threshold)" className="span-12">
        <div className="slider-row">
          <input type="range" min="0" max="100" step="1" value={threshold} onChange={(e) => onThreshold(Number(e.target.value))} />
          <strong className="threshold">{threshold}</strong>
          <span className="muted">Wynik ≥ progu = naruszenie. Zbiór złoty: {items.length} pozycji ({gold.data?.source}).</span>
        </div>
      </Panel>
      <div className="tiles span-12">
        <StatTile label="False Positive" value={cm.fp} color="#e7664c" hint="fałszywe alarmy" />
        <StatTile label="False Negative" value={cm.fn} color="#d6bf57" hint="przeoczone naruszenia" />
        <StatTile label="Precyzja" value={pct(cm.precision)} />
        <StatTile label="Pełność (recall)" value={pct(cm.recall)} />
        <StatTile label="F1" value={pct(cm.f1)} />
      </div>
      <Panel title="Macierz pomyłek" className="span-4">
        <table className="cm">
          <thead><tr><th></th><th>Model: naruszenie</th><th>Model: OK</th></tr></thead>
          <tbody>
            <tr><th>Faktycznie naruszenie</th><td className="good">TP {cm.tp}</td><td className="bad">FN {cm.fn}</td></tr>
            <tr><th>Faktycznie OK</th><td className="bad">FP {cm.fp}</td><td className="good">TN {cm.tn}</td></tr>
          </tbody>
        </table>
      </Panel>
      <Panel title="FP / FN i metryki w funkcji progu" className="span-8">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={curve} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="threshold" tick={{ fontSize: 11, fill: "var(--muted)" }} />
            <YAxis yAxisId="n" tick={{ fontSize: 11, fill: "var(--muted)" }} />
            <YAxis yAxisId="p" orientation="right" domain={[0, 1]} tickFormatter={pct} tick={{ fontSize: 11, fill: "var(--muted)" }} />
            <Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--border)" }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <ReferenceLine yAxisId="n" x={Math.round(threshold / 5) * 5} stroke="var(--accent)" strokeDasharray="4 4" />
            <Line yAxisId="n" dataKey="fp" name="FP" stroke="#e7664c" dot={false} />
            <Line yAxisId="n" dataKey="fn" name="FN" stroke="#d6bf57" dot={false} />
            <Line yAxisId="p" dataKey="precision" name="Precyzja" stroke="#6092c0" dot={false} />
            <Line yAxisId="p" dataKey="recall" name="Pełność" stroke="#54b399" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Panel>
    </div>
  );
}
