import { useEffect, useState } from "react";
import { listFindings } from "../lib/api.js";
import { effectiveFails } from "../lib/metrics.js";
import { MODULES, RISK, STATUS, fmtDate, pct } from "../lib/labels.js";
import FindingDetail from "./FindingDetail.jsx";

const EMPTY = { risk_level: "", status: "", module: "", source: "", min_score: "", q: "" };

export default function Findings({ selected, onSelect, refreshKey }) {
  const [filters, setFilters] = useState(EMPTY);
  const [minConf, setMinConf] = useState(0.5);
  const [data, setData] = useState({ items: [], total: 0 });
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const t = setTimeout(() => {
      listFindings({ ...filters, limit: 200 })
        .then((d) => {
          setData(d);
          setLoaded(true);
          setError(null);
        })
        .catch((e) => setError(e.message));
    }, 200); // debounce wyszukiwania
    return () => clearTimeout(t);
  }, [filters, refreshKey, tick]);

  const set = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }));
  const sources = [...new Set(data.items.map((f) => f.document?.source).filter(Boolean))];

  return (
    <div className="split">
      <section className="card">
        <div className="filters">
          <input type="search" placeholder="Szukaj w treści, tytule, URL…" value={filters.q} onChange={set("q")} />
          <select value={filters.risk_level} onChange={set("risk_level")} aria-label="Ryzyko">
            <option value="">ryzyko: wszystkie</option>
            {Object.entries(RISK).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={filters.module} onChange={set("module")} aria-label="Moduł">
            <option value="">moduł: wszystkie</option>
            {Object.entries(MODULES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={filters.status} onChange={set("status")} aria-label="Status">
            <option value="">status: wszystkie</option>
            {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={filters.source} onChange={set("source")} aria-label="Źródło">
            <option value="">źródło: wszystkie</option>
            {sources.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <input type="number" min="0" max="100" placeholder="score ≥" style={{ width: 90 }}
            value={filters.min_score} onChange={set("min_score")} aria-label="Minimalny score" />
          <button className="btn" onClick={() => setFilters(EMPTY)}>Wyczyść</button>
        </div>

        <div className="slider" style={{ marginBottom: 12 }}>
          <label htmlFor="conf">Próg pewności reguł LLM: <b>{pct(minConf)}</b></label>
          <input id="conf" type="range" min="0" max="1" step="0.05" value={minConf}
            onChange={(e) => setMinConf(Number(e.target.value))} />
          <span className="muted" style={{ fontSize: 12 }}>
            „fail” poniżej progu liczony jako „do weryfikacji”, przeliczane lokalnie
          </span>
        </div>

        {error && <p className="error">Nie udało się pobrać ustaleń: {error}</p>}
        {loaded && <p className="muted" style={{ margin: "0 0 8px" }}>{data.total} ustaleń</p>}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Ryzyko</th>
                <th className="num">Score</th>
                <th>Materiał</th>
                <th>Moduły</th>
                <th className="num">Naruszenia</th>
                <th className="num">Pokrycie</th>
                <th>Status</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((f) => {
                const { fails, uncertain } = effectiveFails(f.rule_results, minConf);
                return (
                  <tr key={f.id} className={`row ${selected === f.id ? "selected" : ""}`} onClick={() => onSelect(f.id)}>
                    <td><span className={`risk ${f.risk_level}`}>{RISK[f.risk_level]}</span></td>
                    <td className="num">{f.risk_score.toFixed(1)}</td>
                    <td className="clip" title={f.document?.title || ""}>
                      <span className="muted">{f.document?.source}</span>{" "}
                      {f.document?.title || f.document?.text_excerpt || f.document_id}
                    </td>
                    <td>{f.modules.join(", ") || "—"}</td>
                    <td className="num">
                      {fails.length}
                      {uncertain.length > 0 && <span className="muted"> (+{uncertain.length}?)</span>}
                    </td>
                    <td className="num">{pct(f.coverage)}</td>
                    <td>{STATUS[f.status]}</td>
                    <td className="muted">{fmtDate(f.created_at)}</td>
                  </tr>
                );
              })}
              {!data.items.length && !error && (
                <tr><td colSpan={8} className="muted">{loaded ? "Brak ustaleń dla wybranych filtrów." : "Ładowanie…"}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <FindingDetail id={selected} minConf={minConf} onChanged={() => setTick((t) => t + 1)} />
    </div>
  );
}
