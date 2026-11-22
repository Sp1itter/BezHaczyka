// Przeglad: liczniki z /stats, ostatnie wyniki, kolejka weryfikacji, najczesciej lamane reguly, trend.
// Wszystko liczy serwer; panel pobiera tylko to, co pokazuje.
import { useState } from "react";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import TrendChart from "../components/charts/TrendChart.jsx";
import { EmptyState, PageHeader, SortableTable } from "../components/ui.jsx";
import VerificationCard from "../components/VerificationCard.jsx";
import RulesPanel from "../components/RulesPanel.jsx";
import { twinIndex } from "../lib/caption.js";
import { OPEN_STATUSES } from "../lib/filters.js";
import { SOURCE } from "../lib/labels.js";
import { COL } from "./columns.jsx";

function SourcesPanel({ bySource }) {
  const rows = Object.entries(bySource || {}).sort((a, b) => b[1] - a[1]);
  return (
    <section className="panel compact-panel feed-panel">
      <div className="panel-head"><h2>Źródła</h2><a className="text-link" href="#/findings">Wyniki</a></div>
      {rows.length ? (
        <div className="feed-list">
          {rows.map(([s, n]) => (
            <div className="feed-row" key={s}>
              <span className="source-name">{SOURCE[s] || s}</span>
              <time>{n} {n === 1 ? "wynik" : "wyników"}</time>
            </div>
          ))}
        </div>
      ) : <EmptyState title="Brak materiałów" size="compact">Źródła pojawią się po pierwszej analizie.</EmptyState>}
    </section>
  );
}

// Karta weryfikacji jednej pozycji kolejki: pelny wynik (reguly, dokument) tylko dla biezacej karty.
function QueueCard({ queue, pick, setPick, onReview, reloadKey }) {
  const index = Math.min(pick, queue.length - 1);
  const item = queue[index];
  const full = useApi(() => api.finding(item.id), [item.id, reloadKey]);
  const f = full.data?.id === item.id ? full.data : item;
  return (
    <VerificationCard finding={f} compact onReview={onReview}
      actionHref={`#/findings/${encodeURIComponent(item.id)}`}
      twin={twinIndex(queue, index)}
      pager={{ index, total: queue.length,
        prev: () => setPick((i) => (i - 1 + queue.length) % queue.length),
        next: () => setPick((i) => (i + 1) % queue.length) }} />
  );
}

export default function Overview({ onRefresh, onReview, reloadKey }) {
  const [pick, setPick] = useState(0);
  const all = useApi(() => api.stats(), [reloadKey]);
  const open = useApi(() => api.stats({ status: OPEN_STATUSES }), [reloadKey]);
  const trend = useApi(() => api.trend(), [reloadKey]);
  const recent = useApi(() => api.findings({ limit: 5 }), [reloadKey]);
  const queueRes = useApi(() => api.findings({ risk_level: "high", status: OPEN_STATUSES }), [reloadKey]);

  const s = all.data || {};
  const openHigh = open.data?.by_risk_level?.high || 0;
  // Kolejka: najwyzszy wynik pierwszy; przy remisie materialy z renderem (maja zrzut jako dowod).
  const rendered = (f) => (["facebook", "instagram", "www"].includes(f.document?.source) ? 0 : 1);
  const queue = [...(queueRes.data?.items || [])].sort((a, b) => b.risk_score - a.risk_score || rendered(a) - rendered(b));
  // Tylko kafelki z wartoscia: zero nic analitykowi nie mowi.
  const kpis = [
    ["Wyniki analizy", s.total, ""],
    ["Wysokie ryzyko", s.by_risk_level?.high, "kpi-high"],
    ["Do decyzji", open.data?.total, ""],
    ["Potwierdzone naruszenia", s.by_status?.confirmed, ""],
  ].filter(([, v]) => v);

  return (
    <>
      <PageHeader title="Przegląd" lead="Bieżący stan analizy reklam inwestycyjnych."
        actions={<div className="pipeline-buttons"><button type="button" className="button secondary" onClick={onRefresh}>Odśwież dane</button></div>} />

      {kpis.length > 0 && (
        <section className="kpi-bar" aria-label="Najważniejsze liczby">
          {kpis.map(([label, value, cls]) => <div key={label} className={cls}><span>{label}</span><strong>{value}</strong></div>)}
        </section>
      )}

      {openHigh > 0 && (
        <div className="notice warning">
          <div><strong>Materiały wysokiego ryzyka czekające na decyzję: {openHigh}</strong></div>
          <a href="#/alerts">Przejdź do alertów</a>
        </div>
      )}

      <div className="overview-grid">
        <section className="panel table-panel recent-reports-panel span-7">
          <div className="panel-head">
            <h2>Ostatnie wyniki analizy</h2>
            <a className="text-link" href="#/findings">Wszystkie wyniki</a>
          </div>
          <SortableTable className="reports-table" columns={[COL.date, COL.title, COL.risk, COL.status]}
            rows={recent.data?.items || []} rowKey={(f) => f.id}
            empty={<EmptyState size="compact">{recent.error ? "Nie udało się pobrać wyników." : "Brak wyników analizy."}</EmptyState>} />
        </section>

        <div className="span-5 grid-cell">
          {queue.length ? (
            <QueueCard queue={queue} pick={pick} setPick={setPick} onReview={onReview} reloadKey={reloadKey} />
          ) : (
            <section className="panel verify-card"><div className="empty-state compact"><strong>Brak materiałów do weryfikacji</strong>
              <p>Otwarte sprawy wysokiego ryzyka pojawią się tutaj.</p></div></section>
          )}
        </div>

        <div className="span-7 grid-cell"><RulesPanel reloadKey={reloadKey} allStats={all} /></div>
        <div className="span-5 grid-cell"><SourcesPanel bySource={s.by_source} /></div>

        <section className="panel compact-panel span-12">
          <div className="panel-head"><h2>Wykryte incydenty w czasie</h2><span className="quiet">liczba wyników dziennie wg poziomu ryzyka</span></div>
          <div className="chart-panel">
            {trend.data?.items?.length
              ? <TrendChart data={trend.data.items} variant="bar" height={200} />
              : <EmptyState size="compact">Wykres pojawi się po pierwszych analizach.</EmptyState>}
          </div>
        </section>
      </div>
    </>
  );
}
