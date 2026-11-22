// Alerty: materialy wysokiego ryzyka (z serwera) i strumien na zywo z /ws/alerts (bez odpytywania).
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { EmptyState, FilterBar, PageHeader, SortableTable } from "../components/ui.jsx";
import { OPEN_STATUSES, toApiFilters } from "../lib/filters.js";
import { fmtDate, sourceLabel } from "../lib/labels.js";
import { num } from "../lib/ui.js";
import { COL } from "./columns.jsx";
import { ALERT_FIELDS } from "./filterFields.js";

export default function Alerts({ query, live, feed, reloadKey }) {
  // Bez wybranego statusu: tylko sprawy otwarte.
  const filters = { ...toApiFilters(query), risk_level: "high", status: query.status || OPEN_STATUSES };
  const key = JSON.stringify(filters);
  const list = useApi(() => api.findings(filters), [key, reloadKey]);
  const rows = list.data?.items || [];
  const total = list.data?.total ?? 0;
  return (
    <>
      <PageHeader title="Alerty" lead="Materiały wysokiego ryzyka czekające na decyzję analityka." />
      <section className="panel compact-panel feed-panel">
        <div className="panel-head"><h2>Na żywo</h2>
          <span className={`live-state ${live ? "on" : "off"}`}>{live ? "połączono" : "łączenie ponownie…"}</span></div>
        {feed.length ? (
          <div className="feed-list">
            {feed.map((a) => (
              <div className="feed-row" key={a.finding_id + (a.received_at || "")}>
                <span className="feed-state failed" aria-label="Wysokie ryzyko" />
                <a className="table-title" href={`#/findings/${encodeURIComponent(a.finding_id)}`}>{num(a.risk_score)} · {a.title || "Materiał bez tytułu"}</a>
                <time>{a.source ? `${sourceLabel(a.source)} · ` : ""}{fmtDate(a.created_at || a.received_at)}</time>
              </div>
            ))}
          </div>
        ) : <EmptyState title="Brak nowych alertów" size="compact">Nowe materiały wysokiego ryzyka pojawią się tu same, bez odświeżania.</EmptyState>}
      </section>
      <FilterBar path="/alerts" query={query} fields={ALERT_FIELDS} />
      <section className="panel table-panel">
        <div className="panel-head"><h2>Do decyzji: {total}</h2>
          {total > rows.length && <a className="text-link" href={`#/findings?risk=high`}>wszystkie w Wynikach</a>}</div>
        {list.error ? <EmptyState title="Nie udało się pobrać alertów">{list.error.message}</EmptyState> : (
          <SortableTable columns={[COL.risk, COL.score, COL.title, COL.status, COL.assignee, COL.date]}
            rows={rows} rowKey={(f) => f.id}
            empty={<EmptyState>{list.loading ? "Ładowanie…" : "Brak otwartych alertów."}</EmptyState>} />
        )}
      </section>
    </>
  );
}
