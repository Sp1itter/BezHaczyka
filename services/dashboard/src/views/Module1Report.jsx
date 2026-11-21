import { useEffect, useState } from "react";
import Panel from "../components/common/Panel.jsx";
import StatTile from "../components/common/StatTile.jsx";
import { api } from "../api/client.js";
import { fmtDate, SOURCE } from "../lib/labels.js";
import { FLAGS, RELATIONS, clip, flagLabel, relationLabel, safeHref, summarize } from "../lib/module1.js";

const EMPTY = { source: "", relation: "", flag: "", since: "" };
const link = (href, text) => (safeHref(href) ? <a href={safeHref(href)} target="_blank" rel="noreferrer">{text}</a> : text);
// Pole daty -> ISO dla parametru since.
const apiFilters = (f) => ({ ...f, since: f.since ? `${f.since}T00:00:00Z` : "" });

// Raport Modulu 1 (GET /reports/module1) z filtrami i eksportem CSV.
export default function Module1Report({ reloadKey }) {
  const [filters, setFilters] = useState(EMPTY);
  const [data, setData] = useState({ items: [], total: 0 });
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false; // odrzuc spozniona odpowiedz po zmianie filtrow
    setLoaded(false);
    api.module1Report(apiFilters(filters))
      .then((d) => { if (!ignore) { setData({ items: d.items || [], total: d.total ?? 0 }); setError(null); } })
      .catch((e) => {
        if (ignore) return;
        setData({ items: [], total: 0 });
        setError(String(e.message).startsWith("503")
          ? "Raport Modułu 1 jest chwilowo niedostępny (widok bazy nie jest gotowy)."
          : "Nie udało się pobrać raportu Modułu 1.");
      })
      .finally(() => { if (!ignore) setLoaded(true); });
    return () => { ignore = true; };
  }, [filters, reloadKey]);

  const set = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }));
  const s = summarize(data.items, data.total);

  return (
    <div className="grid">
      <div className="span-3"><StatTile label="Pozycji" value={s.total} /></div>
      <div className="span-3"><StatTile label="Podmioty trzecie" value={s.thirdParty} hint="na stronie" /></div>
      <div className="span-3"><StatTile label="Bez ujawnienia" value={s.noDisclosure} hint="na stronie" /></div>
      <div className="span-3"><StatTile label="Firmy zagraniczne" value={s.foreign} hint="na stronie" /></div>
      <Panel title="Moduł 1 — raport" className="span-12"
        actions={<a className="btn" href={api.module1CsvUrl(apiFilters(filters))} download>Pobierz CSV</a>}>
        <div className="filterbar" style={{ padding: 0, marginBottom: 12 }}>
          <select value={filters.source} onChange={set("source")} aria-label="Źródło">
            <option value="">źródło: wszystkie</option>
            {Object.entries(SOURCE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={filters.relation} onChange={set("relation")} aria-label="Relacja">
            <option value="">relacja: wszystkie</option>
            {Object.entries(RELATIONS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={filters.flag} onChange={set("flag")} aria-label="Flaga">
            <option value="">flaga: wszystkie</option>
            {Object.entries(FLAGS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <label className="muted">od <input type="date" value={filters.since} onChange={set("since")} /></label>
          <button className="btn link" onClick={() => setFilters(EMPTY)}>Wyczyść</button>
        </div>
        {error && <div className="empty" role="alert">{error}</div>}
        <div style={{ overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr><th>Firma</th><th>Reklamujący</th><th>Relacja</th><th>Flagi</th><th>Treść</th><th>URL</th><th>Pierwsze</th><th>Ostatnie</th><th>W kampanii</th></tr>
            </thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.case_id} style={{ cursor: "default" }}>
                  <td>{r.firm_official_name || r.firm_name_in_ad || "—"}{r.firm_country && <span className="muted"> ({r.firm_country})</span>}</td>
                  <td>{link(r.advertiser_url, r.advertiser_name || r.advertiser_handle || r.advertiser_url || "—")}</td>
                  <td>{relationLabel(r.relation)}</td>
                  <td>
                    {(r.m1_flags || []).map((f) => <span key={f} className="pill" style={{ cursor: "default", marginRight: 4 }}>{flagLabel(f)}</span>)}
                    {!(r.m1_flags || []).length && <span className="muted">—</span>}
                  </td>
                  <td title={r.tresc || ""}>{clip(r.tresc)}</td>
                  <td>{safeHref(r.url) ? link(r.url, "otwórz") : <span title={r.url || ""}>{r.url ? clip(r.url, 30) : "—"}</span>}</td>
                  <td className="muted">{r.first_seen_at ? fmtDate(r.first_seen_at) : "—"}</td>
                  <td className="muted">{r.last_seen_at ? fmtDate(r.last_seen_at) : "—"}</td>
                  <td>{r.campaign_size ?? "—"}</td>
                </tr>
              ))}
              {!data.items.length && !error && (
                <tr><td colSpan={9} className="muted">{loaded ? "Brak pozycji dla wybranych filtrów." : "Ładowanie…"}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
