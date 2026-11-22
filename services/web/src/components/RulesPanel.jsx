// Karta "Najczesciej lamane reguly": liczniki naruszen z GET /stats (failed_rules).
import { useState } from "react";
import { categoryOf } from "../lib/rules.js";

const LIMIT = 5;

// allStats: wynik /stats pobrany juz przez widok nadrzedny.
export default function RulesPanel({ allStats }) {
  const [expanded, setExpanded] = useState(false);
  const total = allStats.data?.total || 0;
  const rows = (allStats.data?.failed_rules || []).map((r) => ({ ...r, category: categoryOf(r.rule_id) }));
  const visible = expanded ? rows : rows.slice(0, LIMIT);

  return (
    <section className="panel table-panel rules-panel">
      <div className="panel-head"><h2>Najczęściej łamane reguły</h2></div>
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
        <div className="empty-state compact"><strong>{allStats.error ? "Nie udało się pobrać danych" : "Brak naruszeń"}</strong></div>
      )}
      {rows.length > LIMIT && (
        <div className="collapse-footer rules-footer">
          <span className="quiet">Pokazano {visible.length} z {rows.length} reguł</span>
          <button type="button" className="button ghost small" aria-expanded={expanded} onClick={() => setExpanded((e) => !e)}>
            {expanded ? "Zwiń" : "Pokaż więcej"}
          </button>
        </div>
      )}
    </section>
  );
}
