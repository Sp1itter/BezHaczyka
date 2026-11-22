// Karta "Najczesciej lamane reguly": liczniki naruszen z GET /stats (failed_rules), filtr zrodla i wyszukiwanie.
import { useState } from "react";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { SOURCE } from "../lib/labels.js";
import { categoryOf } from "../lib/rules.js";

const LIMIT = 5;

// allStats: /stats bez filtrow pobrane juz przez Przeglad (bez filtra zrodla nie pytamy API drugi raz).
export default function RulesPanel({ reloadKey, allStats }) {
  const [q, setQ] = useState("");
  const [source, setSource] = useState("");
  const [expanded, setExpanded] = useState(false);
  const bySource = useApi(() => (source ? api.stats({ source }) : Promise.resolve(null)), [source, reloadKey]);
  const res = source ? bySource : allStats;
  const total = res.data?.total || 0;
  const text = q.trim().toLowerCase();
  const rows = (res.data?.failed_rules || [])
    .map((r) => ({ ...r, category: categoryOf(r.rule_id) }))
    .filter((r) => !text || `${r.rule_id} ${r.rule_name} ${r.category}`.toLowerCase().includes(text));
  const visible = expanded ? rows : rows.slice(0, LIMIT);

  return (
    <section className="panel table-panel rules-panel">
      <div className="panel-head"><h2>Najczęściej łamane reguły</h2></div>
      <form className="rules-filters" onSubmit={(e) => e.preventDefault()}>
        <label className="search-field"><span>Szukaj</span>
          <input type="search" placeholder="Numer lub nazwa reguły" value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
        <label><span>Źródło</span>
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="">Wszystkie</option>
            {Object.entries(SOURCE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
      </form>
      {rows.length ? (
        <div className="table-wrap">
          <table className="rules-table">
            <thead><tr><th>Reguła</th><th>Kategoria</th><th>Liczba wykryć</th></tr></thead>
            <tbody>
              {visible.map((r) => {
                const share = total ? Math.round((r.count / total) * 100) : 0;
                return (
                  <tr key={r.rule_id}>
                    <td><span className="rule-code">{r.rule_id}</span> {r.rule_name}</td>
                    <td className="quiet">{r.category}</td>
                    <td>
                      <div className="rule-count">
                        <strong>{r.count}</strong>
                        <span className="rule-share" title={`${share}% materiałów`}><i style={{ width: `${share}%` }} /></span>
                        <span className="quiet">{share}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state compact"><strong>{res.error ? "Nie udało się pobrać danych" : "Brak naruszeń"}</strong>
          <p>{res.error ? "Sprawdź połączenie z API." : "Dla wybranych filtrów nie wykryto łamania reguł."}</p></div>
      )}
      {rows.length > 0 && (
        <div className="collapse-footer rules-footer">
          <span className="quiet">Pokazano {visible.length} z {rows.length} reguł</span>
          {rows.length > LIMIT && (
            <button type="button" className="button ghost small" aria-expanded={expanded} onClick={() => setExpanded((e) => !e)}>
              {expanded ? "Zwiń" : "Pokaż więcej"}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
