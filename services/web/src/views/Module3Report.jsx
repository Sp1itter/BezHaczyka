// Raport Modulu 3 (GET /reports/module3): podmiot, tresc oferty, URL, status w rejestrze KNF + CSV.
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { EmptyState, PageHeader, RiskBadge, SortableTable, StatusPill } from "../components/ui.jsx";
import { fmtDate, sourceLabel } from "../lib/labels.js";
import { clip, safeHref } from "../lib/module1.js";

const COLUMNS = [
  {
    label: "Typ", type: "text", className: "nowrap", sortValue: (r) => (r.confirmed ? 1 : 0),
    render: (r) => r.confirmed
      ? <StatusPill status="false_positive">naruszenie M3</StatusPill>
      : <StatusPill status="triage">kandydat (spoza rejestru)</StatusPill>,
  },
  { label: "Ryzyko", type: "text", sortValue: (r) => r.risk_score, render: (r) => <RiskBadge level={r.risk_level} /> },
  {
    label: "Podmiot", type: "text", className: "wide-cell", sortValue: (r) => r.entity || r.publisher,
    render: (r) => <><a className="table-title" href={`#/findings/${encodeURIComponent(r.finding_id)}`}>{r.entity || r.publisher || "—"}</a>
      <span className="table-meta">{sourceLabel(r.source)}</span></>,
  },
  { label: "Treść oferty", type: "text", sortValue: (r) => r.offer_text, render: (r) => <span title={r.offer_text || ""}>{clip(r.offer_text) || "—"}</span> },
  {
    label: "URL", type: "text", sortValue: (r) => r.url,
    render: (r) => (safeHref(r.url) ? <a className="text-link" href={safeHref(r.url)} target="_blank" rel="noreferrer noopener">otwórz ↗</a> : "—"),
  },
  { label: "Rejestr KNF", type: "text", sortValue: (r) => r.registry_status, render: (r) => r.registry_status || "—" },
  { label: "Dlaczego", type: "text", sortValue: (r) => r.evidence, render: (r) => <span className="quiet">{r.evidence || "—"}</span> },
  {
    label: "Wykryto", type: "date", className: "nowrap", sortValue: (r) => r.created_at,
    render: (r) => <a className="text-link" href={`#/findings/${encodeURIComponent(r.finding_id)}`}>{fmtDate(r.created_at)}</a>,
  },
  {
    label: "", type: "text", className: "nowrap", sortValue: () => 0,
    render: (r) => <a className="copy-button" href={`#/findings/${encodeURIComponent(r.finding_id)}`}>Szczegóły ›</a>,
  },
];

export default function Module3Report({ reloadKey }) {
  const res = useApi(() => api.module3Report(), [reloadKey]);
  const items = res.data?.items || [];
  const total = res.data?.total ?? items.length;
  const confirmed = items.filter((r) => r.confirmed).length;
  return (
    <>
      <PageHeader title="Raport Modułu 3: doradztwo bez zezwolenia"
        lead="Podmioty spoza rejestru KNF, które oferują doradztwo lub rekomendacje inwestycyjne. Najpierw potwierdzone naruszenia, potem kandydaci do weryfikacji."
        actions={<a className={`button secondary ${total ? "" : "disabled"}`} href={api.module3CsvUrl()} download aria-disabled={!total}>Pobierz CSV</a>} />
      <section className="panel table-panel">
        <div className="panel-head"><h2>Pozycje: {total}</h2>
          {total > 0 && <span className="quiet">{confirmed} potwierdzone · {total - confirmed} kandydatów do weryfikacji</span>}</div>
        {res.error ? <EmptyState title="Nie udało się pobrać raportu">{res.error.message}</EmptyState> : (
          <SortableTable columns={COLUMNS} rows={items} rowKey={(r) => r.finding_id}
            empty={<EmptyState>{res.loading ? "Ładowanie…" : "Brak materiałów z naruszeniem Modułu 3."}</EmptyState>} />
        )}
      </section>
    </>
  );
}
