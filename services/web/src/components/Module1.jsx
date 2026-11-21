import { useEffect, useState } from "react";
import { getModule1Report } from "../lib/api.js";
import { FLAGS, flagLabel, csvUrl, clip, screenshotInfo, summarize } from "../lib/module1.js";
import { RELATION, fmtDate } from "../lib/labels.js";

const EMPTY = { source: "", relation: "", flag: "" };

export default function Module1() {
  const [filters, setFilters] = useState(EMPTY);
  const [data, setData] = useState({ items: [], total: 0 });
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [sources, setSources] = useState([]);

  useEffect(() => {
    getModule1Report(filters)
      .then((d) => {
        setData(d);
        setError(null);
        setSources((s) => [...new Set([...s, ...d.items.map((r) => r.source).filter(Boolean)])]);
      })
      .catch((e) => {
        setData({ items: [], total: 0 });
        setError(e.message);
      })
      .finally(() => setLoaded(true));
  }, [filters]);

  const set = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }));
  const s = summarize(data.items, data.total);

  return (
    <section className="card">
      <div className="filters">
        <select value={filters.source} onChange={set("source")} aria-label="Źródło">
          <option value="">źródło: wszystkie</option>
          {sources.map((x) => <option key={x} value={x}>{x}</option>)}
        </select>
        <select value={filters.relation} onChange={set("relation")} aria-label="Relacja">
          <option value="">relacja: wszystkie</option>
          {Object.entries(RELATION).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filters.flag} onChange={set("flag")} aria-label="Flaga">
          <option value="">flaga: wszystkie</option>
          {Object.entries(FLAGS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <button className="btn" onClick={() => setFilters(EMPTY)}>Wyczyść</button>
        <a className="btn" href={csvUrl(filters)} download>Pobierz CSV</a>
      </div>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", margin: "0 0 12px" }}>
        {[
          ["Pozycji", s.total],
          ["Podmioty trzecie (na stronie)", s.thirdParty],
          ["Bez ujawnienia (na stronie)", s.noDisclosure],
          ["Firmy zagraniczne (na stronie)", s.foreign],
        ].map(([label, n]) => (
          <div key={label} className="pill" style={{ flexDirection: "column", alignItems: "flex-start" }}>
            <b style={{ fontSize: 20 }}>{n}</b>
            <span className="muted">{label}</span>
          </div>
        ))}
      </div>

      {error && <p className="error">{error}</p>}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Firma</th>
              <th>Reklamujący</th>
              <th>Relacja</th>
              <th>Flagi</th>
              <th>Treść</th>
              <th>URL</th>
              <th>Zrzut</th>
              <th>Pierwsze</th>
              <th>Ostatnie</th>
              <th className="num">W kampanii</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((r) => {
              const shot = screenshotInfo(r.screenshot_uri);
              const who = r.advertiser_name || r.advertiser_handle || r.advertiser_url || "—";
              return (
                <tr key={r.case_id}>
                  <td>
                    {r.firm_official_name || r.firm_name_in_ad || "—"}
                    {r.firm_country && <span className="muted"> ({r.firm_country})</span>}
                  </td>
                  <td>
                    {r.advertiser_url
                      ? <a href={r.advertiser_url} target="_blank" rel="noreferrer">{who}</a>
                      : who}
                  </td>
                  <td>{RELATION[r.relation] || r.relation}</td>
                  <td>
                    {(r.m1_flags || []).map((f) => <span key={f} className="pill">{flagLabel(f)}</span>)}
                    {!(r.m1_flags || []).length && <span className="muted">—</span>}
                  </td>
                  <td className="clip" title={r.tresc || ""}>{clip(r.tresc)}</td>
                  <td>{r.url ? <a href={r.url} target="_blank" rel="noreferrer">otwórz</a> : "—"}</td>
                  <td>
                    {!shot ? "—" : shot.href
                      ? <a href={shot.href} target="_blank" rel="noreferrer">zrzut</a>
                      : <span title={r.screenshot_uri}>{shot.name}</span>}
                  </td>
                  <td className="muted">{fmtDate(r.first_seen_at)}</td>
                  <td className="muted">{fmtDate(r.last_seen_at)}</td>
                  <td className="num">{r.campaign_size ?? "—"}</td>
                </tr>
              );
            })}
            {!data.items.length && !error && (
              <tr><td colSpan={10} className="muted">{loaded ? "Brak pozycji dla wybranych filtrów." : "Ładowanie…"}</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
