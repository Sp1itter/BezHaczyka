import { useEffect, useState } from "react";
import { getFinding, setStatus } from "../lib/api.js";
import { MODULES, RELATION, RISK, STATUS, VERDICT, fmtDate, pct } from "../lib/labels.js";

const ORDER = { fail: 0, uncertain: 1, not_applicable: 2, pass: 3 };

function verdictOf(r, minConf) {
  return r.verdict === "fail" && r.confidence < minConf ? "uncertain" : r.verdict;
}

function Evidence({ e }) {
  return (
    <div>
      <div>{e.summary}</div>
      {e.quote && <blockquote>„{e.quote}”</blockquote>}
      {e.measured && (
        <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
          {Object.entries(e.measured).map(([k, v]) => `${k} = ${v}`).join(" · ")}
        </div>
      )}
      {(e.viewport || e.transcript_ts !== null) && (
        <div className="muted" style={{ fontSize: 12 }}>
          {e.viewport && `widok: ${e.viewport}`}
          {e.transcript_ts !== null && e.transcript_ts !== undefined && ` · nagranie: ${e.transcript_ts.toFixed(1)} s`}
        </div>
      )}
    </div>
  );
}

function Module3({ f }) {
  const firm = f.entities.investment_firm;
  const adv = f.entities.advertiser;
  const m3 = f.rule_results.find((r) => r.rule_id === "M3");
  // Podmioty maja znaczenie dla Modulu 1 (relacja reklamujacego) i Modulu 3 (brak autoryzacji).
  if (!f.modules.includes(1) && !f.modules.includes(3) && !m3) return null;
  return (
    <>
      <h3>Podmioty i rejestr KNF</h3>
      <dl className="kv">
        <dt>Firma w reklamie</dt>
        <dd>{firm.name_in_ad || "—"}</dd>
        <dt>Dopasowanie w rejestrze</dt>
        <dd>
          {firm.registry_match?.official_name
            ? `${firm.registry_match.official_name} (${firm.registry_match.knf_id}, zgodność ${pct(firm.registry_match.score)})`
            : "brak dopasowania"}
        </dd>
        <dt>Autoryzacja KNF</dt>
        <dd className={firm.is_authorized ? "" : "error"}>{firm.is_authorized ? "tak" : "nie stwierdzono"}</dd>
        <dt>Reklamujący</dt>
        <dd>{adv.name || "—"} · {RELATION[adv.relation_to_firm]}</dd>
        <dt>Ujawnienie współpracy</dt>
        <dd>{adv.disclosure_found ? "tak" : "nie znaleziono"}</dd>
        {adv.affiliate_link && (<><dt>Link afiliacyjny</dt><dd className="clip">{adv.affiliate_link}</dd></>)}
      </dl>
    </>
  );
}

export default function FindingDetail({ id, minConf, onChanged }) {
  const [f, setF] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!id) return;
    setF(null);
    getFinding(id).then(setF).catch((e) => setError(e.message));
  }, [id]);

  if (!id) return <aside className="card muted">Wybierz ustalenie z tabeli, aby zobaczyć dowody.</aside>;
  if (error) return <aside className="card error">{error}</aside>;
  if (!f) return <aside className="card muted">Ładowanie…</aside>;

  const changeStatus = async (s) => {
    await setStatus(f.id, s);
    setF({ ...f, status: s });
    onChanged();
  };
  const rules = [...f.rule_results].sort(
    (a, b) => ORDER[verdictOf(a, minConf)] - ORDER[verdictOf(b, minConf)] || b.severity - a.severity,
  );
  const doc = f.document || {};

  return (
    <aside className="card">
      <h2 style={{ display: "flex", gap: 12, alignItems: "baseline", flexWrap: "wrap" }}>
        <span className={`risk ${f.risk_level}`}>Ryzyko {RISK[f.risk_level]}</span>
        <span>score {f.risk_score.toFixed(1)}</span>
        <span className="muted" style={{ fontWeight: 400 }}>pokrycie reguł {pct(f.coverage)}</span>
      </h2>
      <div className="bar" title={`Oceniono ${pct(f.coverage)} reguł`}><span style={{ width: pct(f.coverage) }} /></div>
      <p className="muted" style={{ fontSize: 12 }}>
        Reguły „nie oceniono” to brak danych (np. brak renderu lub transkrypcji), nie naruszenie.
      </p>

      <h3>Dlaczego ten moduł</h3>
      <div className="reason">
        <div style={{ fontSize: 12 }} className="muted">
          {f.routing.rule} · brama zakresu: {f.routing.scope_gate} ·{" "}
          {f.modules.map((m) => MODULES[m] || `Moduł ${m}`).join(", ") || "bez modułu"}
        </div>
        {f.routing.reason}
      </div>

      <h3>Materiał</h3>
      <dl className="kv">
        <dt>Źródło</dt><dd>{doc.source || "—"}</dd>
        <dt>Tytuł</dt><dd>{doc.title || "—"}</dd>
        <dt>Publikujący</dt><dd>{doc.publisher?.display_name || doc.publisher?.handle || "—"}</dd>
        <dt>URL</dt><dd className="clip"><a href={doc.url} target="_blank" rel="noreferrer noopener">{doc.url}</a></dd>
        <dt>Zarejestrowano</dt><dd>{fmtDate(f.created_at)}</dd>
      </dl>
      {doc.text_excerpt && <blockquote>{doc.text_excerpt}{doc.text_excerpt.length >= 400 ? "…" : ""}</blockquote>}

      <Module3 f={f} />

      <h3>Reguły ({rules.length})</h3>
      {rules.map((r) => {
        const v = verdictOf(r, minConf);
        return (
          <div className="rule" key={r.rule_id}>
            <header>
              <span className="id">{r.rule_id}</span>
              <span>{r.rule_name}</span>
              <span className={`verdict ${v}`}>{VERDICT[v]}</span>
              <span className="muted" style={{ fontSize: 12 }}>
                {r.engine} · waga {r.severity} · pewność {pct(r.confidence)}
              </span>
            </header>
            {r.legal_basis && <div className="basis">{r.legal_basis}</div>}
            <Evidence e={r.evidence} />
          </div>
        );
      })}

      <h3>Decyzja nadzorcy</h3>
      <div className="filters">
        <span>Status: <b>{STATUS[f.status]}</b></span>
        {["in_review", "confirmed", "dismissed"].map((s) => (
          <button key={s} className={`btn small ${f.status === s ? "primary" : ""}`} onClick={() => changeStatus(s)}>
            {STATUS[s]}
          </button>
        ))}
      </div>
    </aside>
  );
}
