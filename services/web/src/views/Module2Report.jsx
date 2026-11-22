// Raport Modulu 2 (informacja o ryzyku, art. 44): liczniki z GET /stats?module=2, najczesciej
// naruszane wymogi i materialy z najwyzszym wynikiem. Lista pelna: Wyniki z filtrem module=2.
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import Breakdown from "../components/charts/Breakdown.jsx";
import { EmptyState, PageHeader, SortableTable } from "../components/ui.jsx";
import { href } from "../lib/router.js";
import { COL } from "./columns.jsx";

const TOP = 15;

export default function Module2Report({ reloadKey }) {
  const stats = useApi(() => api.stats({ module: 2 }), [reloadKey]);
  const list = useApi(() => api.findings({ module: 2, risk_level: ["high", "medium"], limit: 200 }), [reloadKey]);
  const s = stats.data || {};
  const withBreach = (list.data?.items || []).length;
  const top = [...(list.data?.items || [])].sort((a, b) => b.risk_score - a.risk_score).slice(0, TOP);
  const rules = (s.failed_rules || []).filter((r) => r.rule_id !== "M3").slice(0, 12)
    .map((r) => ({ key: r.rule_id, label: `${r.rule_id}. ${r.rule_name}`, value: r.count }));
  const kpis = [
    ["Ocenione materiały", s.total],
    ["Wysokie ryzyko", s.by_risk_level?.high || 0],
    ["Średnie ryzyko", s.by_risk_level?.medium || 0],
  ];

  return (
    <>
      <PageHeader title="Raport Modułu 2: informacja o ryzyku"
        lead="Czy reklama rzetelnie informuje o ryzyku (art. 44 rozporządzenia 2017/565): które wymogi są najczęściej łamane i gdzie."
        actions={<a className="button secondary" href={href("/findings", { module: 2 })}>Wszystkie materiały M2</a>} />

      {stats.error ? <EmptyState title="Nie udało się pobrać raportu">{stats.error.message}</EmptyState> : (
        <>
          <section className="kpi-bar kpi-3" aria-label="Podsumowanie Modułu 2">
            {kpis.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value ?? "—"}</strong></div>)}
          </section>

          <div className="overview-grid">
            <section className="panel compact-panel span-12">
              <div className="panel-head"><h2>Najczęściej naruszane wymogi</h2><span className="quiet">liczba materiałów z naruszeniem</span></div>
              {rules.length ? <div className="chart-panel"><Breakdown rows={rules} color="#e7664c" /></div>
                : <EmptyState size="compact">{stats.loading ? "Ładowanie…" : "Brak naruszeń."}</EmptyState>}
            </section>

            <section className="panel table-panel span-12">
              <div className="panel-head"><h2>Najpoważniejsze przypadki</h2>
                <span className="quiet">{withBreach ? `${Math.min(TOP, withBreach)} z ${withBreach} o ryzyku wysokim lub średnim` : ""}</span></div>
              <SortableTable columns={[COL.date, COL.title, COL.risk, COL.score, COL.status]} rows={top} rowKey={(f) => f.id}
                empty={<EmptyState>{list.loading ? "Ładowanie…" : "Brak materiałów o podwyższonym ryzyku."}</EmptyState>} />
            </section>
          </div>
        </>
      )}
    </>
  );
}
