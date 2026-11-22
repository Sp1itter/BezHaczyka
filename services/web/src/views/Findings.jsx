// Wyniki: filtry z adresu (#/findings?risk=high&...) przekazywane do GET /findings, stronicowanie po stronie serwera.
import { api, PAGE_SIZE } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import TrendChart from "../components/charts/TrendChart.jsx";
import { EmptyState, FilterDrawer, PageHeader, SortableTable } from "../components/ui.jsx";
import { toApiFilters } from "../lib/filters.js";
import { href } from "../lib/router.js";
import { COL } from "./columns.jsx";
import { FILTER_FIELDS } from "./filterFields.js";

export default function Findings({ query, reloadKey }) {
  const filters = toApiFilters(query);
  const page = Math.max(1, Number(query.page) || 1);
  const key = JSON.stringify(filters);
  const list = useApi(() => api.findings({ ...filters, offset: (page - 1) * PAGE_SIZE }), [key, page, reloadKey]);
  const trend = useApi(() => api.trend(filters), [key, reloadKey]);
  const total = list.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageHref = (p) => href("/findings", { ...query, page: p > 1 ? p : "" });

  return (
    <>
      <PageHeader title="Wyniki analizy" lead="Wszystkie ocenione materiały. Filtry działają po stronie serwera." />
      <section className="panel table-panel">
        <div className="panel-head"><h2>Wyniki: {total}</h2>
          <span className="quiet">{total ? `strona ${page} z ${pages} · najnowsze pierwsze` : ""}</span></div>
        <FilterDrawer path="/findings" query={{ ...query, page: "" }} fields={FILTER_FIELDS} resultCount={total} defaultOpen />
        {list.error ? <EmptyState title="Nie udało się pobrać wyników">{list.error.message}</EmptyState> : (
          <SortableTable columns={[COL.date, COL.title, COL.modules, COL.violations, COL.risk, COL.score, COL.status]}
            rows={list.data?.items || []} rowKey={(f) => f.id}
            empty={<EmptyState>{list.loading ? "Ładowanie…" : "Brak wyników dla wybranych filtrów."}</EmptyState>} />
        )}
        {pages > 1 && (
          <nav className="pager" aria-label="Strony wyników">
            {page > 1 ? <a className="button ghost small" href={pageHref(page - 1)}>‹ Poprzednia</a> : <span />}
            <span className="quiet">{(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} z {total}</span>
            {page < pages ? <a className="button ghost small" href={pageHref(page + 1)}>Następna ›</a> : <span />}
          </nav>
        )}
      </section>
      <section className="panel table-panel top-gap">
        <div className="panel-head"><h2>Wykryte incydenty w czasie</h2><span className="quiet">te same filtry, wg poziomu ryzyka</span></div>
        <div className="chart-panel">
          {trend.data?.items?.length
            ? <TrendChart data={trend.data.items} variant="bar" height={200} />
            : <EmptyState size="compact">Brak danych do wykresu.</EmptyState>}
        </div>
      </section>
    </>
  );
}
