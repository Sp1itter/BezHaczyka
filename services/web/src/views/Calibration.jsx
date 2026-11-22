// Kalibracja progu na zbiorze zlotym (GET /calibration) i zapis progu alertow (PUT /settings/threshold).
import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { EmptyState, PageHeader, SortableTable } from "../components/ui.jsx";
import { confusion, sweep } from "../lib/calibration.js";
import { num, pct } from "../lib/ui.js";

const OUTCOME = { TP: "trafienie", FP: "fałszywy alarm", FN: "przeoczenie", TN: "poprawnie pominięty" };
const outcome = (it, t) => (typeof it.score !== "number" ? null
  : it.score >= t ? (it.is_violation ? "TP" : "FP") : it.is_violation ? "FN" : "TN");

export default function Calibration({ analyst, toast }) {
  const gold = useApi(() => api.calibration(), []);
  const saved = useApi(() => api.threshold(), []);
  const [threshold, setThreshold] = useState(50);
  const [saving, setSaving] = useState(false);
  useEffect(() => { if (typeof saved.data?.value === "number") setThreshold(saved.data.value); }, [saved.data]);

  const items = useMemo(() => (gold.data?.items || []).filter((i) => typeof i.score === "number"), [gold.data]);
  const cm = useMemo(() => confusion(items, threshold), [items, threshold]);
  const curve = useMemo(() => sweep(items, 1), [items]);
  const best = curve.reduce((b, r) => (r.f1 > (b?.f1 ?? -1) ? r : b), null);
  const savedValue = saved.data?.value;

  const save = async () => {
    setSaving(true);
    try {
      await api.saveThreshold(threshold, analyst);
      saved.reload();
      toast(`Próg alertów zapisany: ${num(threshold, 0)} pkt.`, "success");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    { label: "Przypadek", type: "text", className: "case-id", sortValue: (i) => i.id, render: (i) => <code>{i.id}</code> },
    { label: "Wynik", type: "number", sortValue: (i) => i.score, render: (i) => <span className="mono">{num(i.score)}</span> },
    { label: "Ocena człowieka", type: "text", sortValue: (i) => String(i.is_violation), render: (i) => (i.is_violation ? "naruszenie" : "bez naruszenia") },
    {
      label: "Przy tym progu", type: "text", sortValue: (i) => outcome(i, threshold),
      render: (i) => {
        const o = outcome(i, threshold);
        return <span className={`status ${o === "TP" || o === "TN" ? "approved" : "false_positive"}`}>{OUTCOME[o]}</span>;
      },
    },
    { label: "Uzasadnienie etykiety", type: "text", className: "scenario-cell", sortValue: (i) => i.note, render: (i) => <span>{i.note}</span> },
  ];

  if (gold.error) return <><PageHeader title="Kalibracja progu" /><EmptyState title="Brak zbioru referencyjnego">{gold.error.message}</EmptyState></>;
  return (
    <>
      <PageHeader title="Kalibracja progu" lead={`Zbiór referencyjny: ${items.length} materiałów ocenionych przez człowieka.`} />

      <section className="panel calib-panel">
        <div className="calib-controls">
          <label className="search-field">
            <span>Próg alertu: <strong>{num(threshold, 0)} pkt</strong> (wynik ≥ progu = alert)</span>
            <input type="range" min="0" max="100" step="1" value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} aria-label="Próg alertu" />
          </label>
          {best && <button type="button" className="button ghost" onClick={() => setThreshold(best.threshold)}>Najlepsze F1: {best.threshold} pkt</button>}
          <button type="button" className="button primary" disabled={saving || threshold === savedValue} onClick={save}>
            {threshold === savedValue ? "Próg zapisany" : "Zapisz próg alertów"}
          </button>
        </div>
        <p className="section-note">Wynik o poziomie „wysokie” ma zawsze co najmniej 70 punktów, więc próg poniżej 70 nie ukrywa żadnego wysokiego wyniku, tylko zmienia liczbę alertów dla średnich i niskich.
          {typeof savedValue === "number" ? ` Zapisany próg: ${num(savedValue, 0)} pkt.` : " Bez zapisanego progu alertem jest każdy wynik „wysokie”."}</p>

        <div className="calib-grid">
          <table className="confusion" aria-label="Macierz pomyłek">
            <thead><tr><th /><th>Człowiek: naruszenie</th><th>Człowiek: bez naruszenia</th></tr></thead>
            <tbody>
              <tr><th>Alert</th><td className="hit"><strong>{cm.tp}</strong> trafienia (TP)</td><td className="miss"><strong>{cm.fp}</strong> fałszywe alarmy (FP)</td></tr>
              <tr><th>Bez alertu</th><td className="miss"><strong>{cm.fn}</strong> przeoczenia (FN)</td><td className="hit"><strong>{cm.tn}</strong> poprawnie (TN)</td></tr>
            </tbody>
          </table>
          <div className="qg-metrics">
            <article><span>Precyzja</span><strong>{pct(cm.precision)}</strong></article>
            <article><span>Pełność</span><strong>{pct(cm.recall)}</strong></article>
            <article><span>F1</span><strong>{pct(cm.f1)}</strong></article>
          </div>
        </div>

        <div className="qg-failures">
          <div className="qg-failures-head"><h3>Fałszywe alarmy i przeoczenia a próg</h3><span className="quiet">przerywana linia: bieżący próg</span></div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={curve} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="threshold" type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "var(--muted)" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--muted)" }} />
              <Tooltip labelFormatter={(t) => `próg ${t} pkt`} contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <ReferenceLine x={threshold} stroke="var(--link)" strokeDasharray="4 4" />
              <Line dataKey="fp" name="Fałszywe alarmy (FP)" stroke="#d29a2a" dot={false} isAnimationActive={false} type="stepAfter" />
              <Line dataKey="fn" name="Przeoczenia (FN)" stroke="#c2414b" dot={false} isAnimationActive={false} type="stepAfter" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel table-panel ground-truth-table top-gap">
        <div className="panel-head"><h2>Przypadki referencyjne: {items.length}</h2></div>
        <SortableTable columns={columns} rows={items} rowKey={(i) => i.id}
          empty={<EmptyState>Brak pozycji w zbiorze referencyjnym.</EmptyState>} />
      </section>
    </>
  );
}
