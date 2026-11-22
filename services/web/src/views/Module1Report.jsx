// Raport Modulu 1 (GET /reports/module1): firma, reklamujacy, tresc, URL, platforma, ostatnio widziane + CSV.
import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { EmptyState, FilterBar, PageHeader, SortableTable } from "../components/ui.jsx";
import { fmtDate, SOURCE, sourceLabel } from "../lib/labels.js";
import { FLAGS, RELATIONS, clip, flagLabel, relationLabel, safeHref, summarize } from "../lib/module1.js";

const FIELDS = [
  { name: "source", label: "Źródło", type: "select", options: SOURCE },
  { name: "relation", label: "Relacja", type: "select", options: RELATIONS },
  { name: "flag", label: "Flaga", type: "select", options: FLAGS },
  { name: "since", label: "Od", type: "date" },
];

const COLUMNS = [
  {
    label: "Firma", type: "text", className: "wide-cell", sortValue: (r) => r.firm_official_name || r.firm_name_in_ad,
    render: (r) => <><span className="table-title plain">{r.firm_official_name || r.firm_name_in_ad || "—"}</span>
      {r.firm_country && <span className="table-meta">{r.firm_country}</span>}</>,
  },
  {
    label: "Reklamujący", type: "text", sortValue: (r) => r.advertiser_name || r.advertiser_handle,
    render: (r) => {
      const text = r.advertiser_name || r.advertiser_handle || r.advertiser_url || "—";
      return safeHref(r.advertiser_url) ? <a className="text-link" href={safeHref(r.advertiser_url)} target="_blank" rel="noreferrer noopener">{text}</a> : text;
    },
  },
  { label: "Relacja", type: "text", sortValue: (r) => r.relation, render: (r) => relationLabel(r.relation) },
  {
    label: "Flagi", type: "text", sortValue: (r) => (r.m1_flags || []).join(","),
    render: (r) => ((r.m1_flags || []).length
      ? <div className="tag-list">{r.m1_flags.map((f) => <span className="tag" key={f}>{flagLabel(f)}</span>)}</div>
      : <span className="muted-value">—</span>),
  },
  { label: "Treść", type: "text", sortValue: (r) => r.tresc, render: (r) => <span title={r.tresc || ""}>{clip(r.tresc)}</span> },
  {
    label: "URL", type: "text", sortValue: (r) => r.url,
    render: (r) => (safeHref(r.url) ? <a className="text-link" href={safeHref(r.url)} target="_blank" rel="noreferrer noopener">otwórz ↗</a> : "—"),
  },
  {
    label: "Platforma", type: "text", sortValue: (r) => (r.platformy || []).join(",") || r.source,
    render: (r) => ((r.platformy || []).length ? r.platformy.map((x) => x.charAt(0) + x.slice(1).toLowerCase()).join(", ") : sourceLabel(r.source)),
  },
  { label: "Ostatnio widziane", type: "date", className: "nowrap", sortValue: (r) => r.last_seen_at, render: (r) => (r.last_seen_at ? fmtDate(r.last_seen_at) : "—") },
];

export default function Module1Report({ query, reloadKey }) {
  const [data, setData] = useState({ items: [], total: 0 });
  const [state, setState] = useState("loading");
  const filters = { source: query.source || "", relation: query.relation || "", flag: query.flag || "",
    since: query.since ? `${query.since}T00:00:00Z` : "" };
  const key = JSON.stringify(filters);

  useEffect(() => {
    let ignore = false; // odrzuc spozniona odpowiedz po zmianie filtrow
    setState("loading");
    api.module1Report(filters)
      .then((d) => { if (!ignore) { setData({ items: d.items || [], total: d.total ?? 0 }); setState("ok"); } })
      .catch((e) => { if (!ignore) { setData({ items: [], total: 0 }); setState(e.status === 503 ? "unavailable" : "error"); } });
    return () => { ignore = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, reloadKey]);

  const s = summarize(data.items, data.total);
  const kpis = [["Pozycji", s.total], ["Podmioty trzecie", s.thirdParty], ["Bez ujawnienia współpracy", s.noDisclosure],
    ["Firmy zagraniczne", s.foreign]].filter(([, v]) => v);
  return (
    <>
      <PageHeader title="Raport Modułu 1: podmioty" lead="Firmy inwestycyjne w reklamach, kto je reklamuje i czy ujawnia współpracę."
        actions={<a className="button secondary" href={api.module1CsvUrl(filters)} download>Pobierz CSV</a>} />
      {kpis.length > 0 && (
        <section className="kpi-bar" aria-label="Podsumowanie raportu">
          {kpis.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}
        </section>
      )}
      <FilterBar path="/module1" query={query} fields={FIELDS} />
      <section className="panel table-panel">
        <div className="panel-head"><h2>Pozycje: {data.total}</h2></div>
        {state === "unavailable" && <EmptyState title="Raport chwilowo niedostępny">Baza raportu Modułu 1 nie jest jeszcze gotowa.</EmptyState>}
        {state === "error" && <EmptyState title="Nie udało się pobrać raportu">Sprawdź połączenie z API i odśwież widok.</EmptyState>}
        {state === "loading" && <EmptyState title="Ładowanie…" size="compact" />}
        {state === "ok" && <SortableTable columns={COLUMNS} rows={data.items} rowKey={(r) => r.case_id}
          empty={<EmptyState>Brak pozycji dla wybranych filtrów.</EmptyState>} />}
      </section>
    </>
  );
}
