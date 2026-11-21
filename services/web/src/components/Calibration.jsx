import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getCalibration } from "../lib/api.js";
import { bestF1, confusion, scores, sweep } from "../lib/metrics.js";
import { pct } from "../lib/labels.js";

// Sloty 1-3 palety kategorialnej w stalej kolejnosci (walidowane: CVD i kontrast, tryb jasny i ciemny).
const SERIES = [
  ["precision", "Precyzja", "var(--series-1)"],
  ["recall", "Czułość", "var(--series-2)"],
  ["f1", "F1", "var(--series-3)"],
];
const axis = { stroke: "var(--axis)", tick: { fill: "var(--muted)", fontSize: 12 } };

export default function Calibration() {
  const [gold, setGold] = useState(null);
  const [error, setError] = useState(null);
  const [threshold, setThreshold] = useState(50);

  useEffect(() => {
    getCalibration().then(setGold).catch((e) => setError(e.message));
  }, []);

  const rows = useMemo(() => (gold ? sweep(gold.items) : []), [gold]);
  if (error) return <p className="error">{error}</p>;
  if (!gold) return <p className="muted">Ładowanie…</p>;
  if (!gold.available) return <p className="muted">Brak zbioru złotego ({gold.source}).</p>;

  // Wszystko ponizej liczy sie lokalnie przy kazdym ruchu suwaka.
  const m = confusion(gold.items, threshold);
  const s = scores(m);
  const best = bestF1(rows);
  const scored = gold.items.filter((i) => typeof i.score === "number");

  return (
    <div className="grid">
      <section className="card">
        <h2>Próg flagowania materiału</h2>
        <div className="slider">
          <label htmlFor="thr">Flaguj, gdy score ≥ <b>{threshold}</b></label>
          <input id="thr" type="range" min="0" max="100" value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))} />
          {best && (
            <button className="btn small" onClick={() => setThreshold(best.threshold)}>
              najlepszy F1: próg {best.threshold} ({best.f1.toFixed(2)})
            </button>
          )}
        </div>
        <p className="muted" style={{ fontSize: 12 }}>
          Zbiór złoty: {gold.items.length} materiałów, {scored.length} z wynikiem analizatora
          {m.skipped ? `, ${m.skipped} pominięto (brak score)` : ""}. Etykiety nadane przez człowieka z treści,
          bez patrzenia na score. Mały zbiór: jedna etykieta przesuwa F1 o kilka dziesiątych.
        </p>
      </section>

      <div className="grid two">
        <section className="card">
          <h2>Macierz pomyłek</h2>
          <div className="cm">
            <div className="h" />
            <div className="h">naruszenie (człowiek)</div>
            <div className="h">zgodne (człowiek)</div>
            <div className="h">oflagowane</div>
            <div><div className="big">{m.tp}</div>TP</div>
            <div><div className="big">{m.fp}</div>FP · fałszywy alarm</div>
            <div className="h">nieoflagowane</div>
            <div><div className="big">{m.fn}</div>FN · przeoczenie</div>
            <div><div className="big">{m.tn}</div>TN</div>
          </div>
          <table style={{ marginTop: 16, maxWidth: 360 }}>
            <tbody>
              <tr><td>Precyzja</td><td className="num">{pct(s.precision)}</td></tr>
              <tr><td>Czułość</td><td className="num">{pct(s.recall)}</td></tr>
              <tr><td>F1</td><td className="num">{s.f1 === null ? "—" : s.f1.toFixed(3)}</td></tr>
            </tbody>
          </table>
        </section>

        <section className="card">
          <h2>Metryki w funkcji progu</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={rows} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--grid)" />
              <XAxis dataKey="threshold" type="number" domain={[0, 100]} {...axis} />
              <YAxis domain={[0, 1]} tickFormatter={(v) => pct(v)} {...axis} />
              <Tooltip
                formatter={(v) => (v === null ? "—" : pct(v))}
                labelFormatter={(t) => `próg ${t}`}
                contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--ink)" }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: "var(--ink-2)" }} />
              <ReferenceLine x={threshold} stroke="var(--ink-2)" strokeDasharray="3 3" />
              {SERIES.map(([key, name, color]) => (
                <Line key={key} dataKey={key} name={name} stroke={color} strokeWidth={2} dot={false}
                  connectNulls={false} isAnimationActive={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </section>
      </div>

      <section className="card">
        <h2>Pozycje zbioru złotego przy progu {threshold}</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th><th className="num">Score</th><th className="num">Pokrycie</th>
                <th>Człowiek</th><th>System</th><th>Wynik</th><th>Uzasadnienie etykiety</th>
              </tr>
            </thead>
            <tbody>
              {gold.items.map((it) => {
                const has = typeof it.score === "number";
                const flagged = has && it.score >= threshold;
                const outcome = !has ? "—" : flagged ? (it.is_violation ? "TP" : "FP") : it.is_violation ? "FN" : "TN";
                return (
                  <tr key={it.id} style={{ cursor: "default" }}>
                    <td className="muted">{it.id}</td>
                    <td className="num">{has ? it.score.toFixed(1) : "—"}</td>
                    <td className="num">{pct(it.coverage)}</td>
                    <td>{it.is_violation ? "naruszenie" : "zgodne"}</td>
                    <td>{has ? (flagged ? "oflagowane" : "—") : "brak score"}</td>
                    <td><b>{outcome}</b></td>
                    <td className="clip" title={it.note || ""}>{it.note}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
