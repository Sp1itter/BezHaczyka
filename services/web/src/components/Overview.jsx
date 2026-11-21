import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getStats } from "../lib/api.js";
import { MODULES, RISK, STATUS } from "../lib/labels.js";

// Poziom ryzyka = kolor statusu (zarezerwowany), zawsze z etykieta tekstowa.
const RISK_COLOR = { low: "var(--good)", medium: "var(--warning)", high: "var(--critical)" };
const axis = { stroke: "var(--axis)", tick: { fill: "var(--muted)", fontSize: 12 } };
const tooltipStyle = {
  contentStyle: { background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--ink)" },
  cursor: { fill: "var(--surface-2)" },
};

function Tile({ label, value }) {
  return (
    <div className="card tile">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}

export default function Overview({ refreshKey }) {
  const [s, setS] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    getStats().then(setS).catch((e) => setError(e.message));
  }, [refreshKey]);

  if (error) return <p className="error">{error}</p>;
  if (!s) return <p className="muted">Ładowanie…</p>;

  const risk = ["high", "medium", "low"].map((k) => ({ key: k, name: RISK[k], value: s.by_risk_level[k] || 0 }));
  const rules = s.failed_rules.slice(0, 10).map((r) => ({ name: `${r.rule_id} ${r.rule_name}`, value: r.count }));

  return (
    <div className="grid">
      <div className="grid tiles">
        <Tile label="Ustalenia" value={s.total} />
        <Tile label="Wysokie ryzyko" value={s.by_risk_level.high || 0} />
        <Tile label="Do decyzji (nowe + triage)" value={(s.by_status.new || 0) + (s.by_status.triage || 0)} />
        <Tile label="Potwierdzone" value={s.by_status.confirmed || 0} />
      </div>

      <div className="grid two">
        <section className="card">
          <h2>Ustalenia według poziomu ryzyka</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={risk} margin={{ top: 16, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--grid)" />
              <XAxis dataKey="name" {...axis} />
              <YAxis allowDecimals={false} {...axis} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="value" name="ustalenia" radius={[4, 4, 0, 0]} maxBarSize={56}>
                {risk.map((r) => <Cell key={r.key} fill={RISK_COLOR[r.key]} />)}
                <LabelList dataKey="value" position="top" fill="var(--ink-2)" fontSize={12} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </section>

        <section className="card">
          <h2>Najczęściej naruszane reguły</h2>
          {rules.length === 0 ? (
            <p className="muted">Brak naruszeń w bazie.</p>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(160, rules.length * 32)}>
              <BarChart data={rules} layout="vertical" margin={{ top: 0, right: 32, left: 8, bottom: 0 }}>
                <CartesianGrid horizontal={false} stroke="var(--grid)" />
                <XAxis type="number" allowDecimals={false} {...axis} />
                <YAxis type="category" dataKey="name" width={190} {...axis} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="value" name="naruszenia" fill="var(--series-1)" radius={[0, 4, 4, 0]} maxBarSize={20}>
                  <LabelList dataKey="value" position="right" fill="var(--ink-2)" fontSize={12} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>
      </div>

      <div className="grid two">
        <section className="card">
          <h2>Moduły</h2>
          <table>
            <tbody>
              {Object.entries(MODULES).map(([k, v]) => (
                <tr key={k}><td>{v}</td><td className="num">{s.by_module[k] || 0}</td></tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="card">
          <h2>Statusy i źródła</h2>
          <table>
            <tbody>
              {Object.entries(s.by_status).map(([k, v]) => (
                <tr key={k}><td>{STATUS[k] || k}</td><td className="num">{v}</td></tr>
              ))}
              {Object.entries(s.by_source).map(([k, v]) => (
                <tr key={k}><td className="muted">źródło: {k}</td><td className="num">{v}</td></tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
