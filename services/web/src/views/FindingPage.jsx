// Szczegoly findingu: port report.html wzorca (baner, karta weryfikacji ze zrzutem materialu,
// uklad report-main / report-aside). Tresci reklam sa niezaufane: tylko tekst, linki przez safeHttpUrl.
import { Fragment, useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { CopyButton, ErrorState, PageHeader, RiskBadge } from "../components/ui.jsx";
import VerificationCard from "../components/VerificationCard.jsx";
import { formatEvidence, safeHttpUrl } from "../lib/evidence.js";
import { GROUPS, RELATION, VERDICT, groupOf } from "../lib/detail.js";
import { ANALYSTS, DECISION, MODULE, STATUS, fmtDate, publisherName, sourceLabel } from "../lib/labels.js";
import { num, pct, shortId } from "../lib/ui.js";

const yn = (v) => (v == null ? "—" : v ? "tak" : "nie");
const DECISION_CLASS = { confirmed: "approve", dismissed: "reject" };

// Etykiety ocen z API maja skroty (TP)/(FP)/(FN) - analitykowi wystarczy opis.
const plainLabel = (s) => String(s || "").replace(/\s*\((TP|FP|FN|TN)\)/g, "");

function describeEvent(e, labels) {
  const d = e.detail || {};
  if (e.action === "assign") return d.assignee ? `przypisano: ${d.assignee}` : "zwolniono przypisanie";
  if (e.action === "review") {
    const name = plainLabel(labels.find((l) => l.value === d.label)?.label || d.label);
    return `decyzja: ${name}${d.note ? ` („${d.note}”)` : ""}`;
  }
  if (e.action === "status") return `status: ${STATUS[d.status] || d.status}`;
  return e.action;
}

function ReviewPanel({ f, labels, analyst, onReview }) {
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const decide = async (l) => {
    if (l.value === "other" && !note.trim()) { setError("Dla etykiety „Inny” opisz błąd w notatce."); return; }
    if (!window.confirm(`Czy na pewno zapisać ocenę „${l.label}”?`)) return;
    setBusy(true);
    setError("");
    try {
      await onReview(f.id, l.value, note.trim());
      setNote("");
    } catch (e) {
      setError(e.message || "Nie udało się zapisać decyzji.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="panel review-panel" id="review">
      <h2>Ocena człowieka</h2>
      <p>Decyzja trafia do historii zmian tego materiału.</p>
      {f.ai_suggestion && (
        <p className="ai-note">Sugestia AI: {DECISION[f.ai_suggestion.status] || f.ai_suggestion.status} · {pct(f.ai_suggestion.confidence)}. Decyzję podejmuje człowiek.</p>
      )}
      <div className="authenticated-analyst"><span>Zalogowany analityk</span><strong>{analyst}</strong></div>
      <label><span>Notatka</span>
        <textarea rows="4" maxLength="2000" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Podstawa decyzji, dodatkowe ustalenia…" />
      </label>
      <div className="decision-grid">
        {labels.map((l) => (
          <button key={l.value} type="button" disabled={busy} className={`decision ${DECISION_CLASS[l.verdict] || "enrich"}`}
            onClick={() => decide(l)}>{plainLabel(l.label)}</button>
        ))}
      </div>
      <p className="form-error">{error}</p>
    </section>
  );
}

function DecisionSummary({ f, labels, onEdit }) {
  const label = plainLabel(labels.find((l) => l.value === f.review.label)?.label || f.review.label);
  return (
    <section className="panel decision-summary">
      <h2>Decyzja analityka</h2>
      <p className={`status ${f.review.decision === "confirmed" ? "approved" : "false_positive"}`}>{DECISION[f.review.decision]} · {label}</p>
      {f.review.note && <blockquote>{f.review.note}</blockquote>}
      <p>Zapisał: {f.review.by} · {fmtDate(f.review.at)}</p>
      <button type="button" className="button ghost small" onClick={onEdit}>Zmień ocenę</button>
    </section>
  );
}

function RulesTable({ rules }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Reguła</th><th>Wynik</th><th>Podstawa prawna</th><th>Pewność</th></tr></thead>
        <tbody>
          {rules.map((r) => (
            <tr key={r.rule_id}>
              <td>{r.rule_id}. {r.rule_name}</td>
              <td>{r.verdict === "fail" ? <span className="status failed">{VERDICT.fail}</span> : <span className="quiet">{VERDICT[r.verdict] || r.verdict}</span>}</td>
              <td>{r.legal_basis || <span className="muted-value">—</span>}</td>
              <td className="nowrap">{r.verdict === "not_applicable" ? <span className="muted-value">—</span> : pct(r.confidence)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function FindingPage({ id, labels, analyst, onReview, onAssign, onStatus, toast, reloadKey }) {
  const fin = useApi(() => api.finding(id), [id, reloadKey]);
  const ev = useApi(() => api.events(id), [id, reloadKey]);
  const [editing, setEditing] = useState(false);
  useEffect(() => setEditing(false), [id]);

  if (fin.error) return <><PageHeader title="Wynik niedostępny" lead={fin.error.message} /><ErrorState message={`Nie znaleziono wyniku ${id} albo API jest niedostępne.`} /></>;
  const f = fin.data;
  if (!f) return <PageHeader title="Ładowanie wyniku…" lead={`BH-${shortId(id)}`} />;

  const doc = f.document || {};
  const rules = f.rule_results || [];
  const failed = rules.filter((r) => r.verdict === "fail").sort((a, b) => (b.severity ?? 0) - (a.severity ?? 0));
  const other = rules.filter((r) => r.verdict !== "fail"); // zgodne i nieocenione: zwiniete
  const firm = f.entities?.investment_firm;
  const adv = f.entities?.advertiser;
  const url = safeHttpUrl(doc.url);
  const events = ev.data?.items || [];

  return (
    <>
      <PageHeader title={doc.title || "Bez tytułu"} lead={`${sourceLabel(doc.source)} · wykryto ${fmtDate(f.created_at)}`}
        actions={<a className="button secondary" href="#/alerts">Wróć do alertów</a>} />

      <section className={`report-banner ${f.risk_level}`}>
        <div>
          <span className="report-label">Poziom ryzyka</span>
          <strong>{num(f.risk_score)}</strong>
        </div>
        <dl>
          <div><dt>Poziom</dt><dd><RiskBadge level={f.risk_level} /></dd></div>
          <div><dt>Ocenione reguły</dt><dd>{pct(f.coverage)}</dd></div>
          <div><dt>Moduły</dt><dd>{f.modules?.length ? f.modules.map((m) => MODULE[m] || `M${m}`).join(", ") : "Brak"}</dd></div>
          <div><dt>Status / przypisanie</dt><dd>{STATUS[f.status] || f.status} / {f.assignee || "nieprzypisane"}</dd></div>
        </dl>
      </section>

      <VerificationCard finding={f} actionHref="#review"
        onAction={() => document.getElementById("review")?.scrollIntoView({ behavior: "smooth", block: "start" })} />

      <div className="report-layout">
        <div className="report-main">
          <section className="panel report-section">
            <h2>Naruszenia ({failed.length})</h2>
            {failed.length ? (
              <div className="evidence-list">
                {failed.map((r) => {
                  const e = formatEvidence(r.evidence);
                  return (
                    <article className="evidence-item" key={r.rule_id}>
                      <h3 className="evidence-rule">Reguła {r.rule_id}: {r.rule_name}</h3>
                      {e.quote && <blockquote>{e.quote}</blockquote>}
                      <p>{e.summary || "Opis dowodu niedostępny."}</p>
                      <p className="section-note">Podstawa prawna: {r.legal_basis || "art. 44 rozporządzenia delegowanego 2017/565"}{e.timestamp ? ` · w nagraniu: ${e.timestamp}` : ""}</p>
                      {e.screenshot && <a href={e.screenshot} target="_blank" rel="noreferrer noopener"><img className="evidence-shot" src={e.screenshot} alt={`Wycinek dowodu reguły ${r.rule_id}`} /></a>}
                    </article>
                  );
                })}
              </div>
            ) : <p className="muted-copy">Nie wykryto naruszeń reguł w tym materiale.</p>}
          </section>

          <section className="panel report-section">
            <h2>Podsumowanie</h2>
            <p className="executive-summary">{f.summary || (failed.length
              ? `Wykryto naruszenia: ${failed.map((r) => r.rule_name).join(", ")}. Szczegóły poniżej.`
              : "Nie wykryto naruszeń reguł.")}</p>
            <div className="context-grid">
              <div><span>Publikujący</span><strong>{publisherName(doc) || "Brak wskazania"}</strong></div>
              <div><span>Firma w reklamie</span><strong>{firm?.name_in_ad || "Brak wskazania"}</strong></div>
            </div>
          </section>

          <section className="panel report-section">
            <h2>Materiał</h2>
            <p className="section-note">Treść reklamy jest niezaufana: pokazujemy ją jako tekst, bez wykonywania linków.</p>
            {doc.text_excerpt ? <p className="executive-summary">{doc.text_excerpt}{doc.text_excerpt.length >= 400 ? "…" : ""}</p> : <p className="muted-copy">Brak tekstu materiału.</p>}
            {doc.url && (
              <div className="ioc-list">
                <div className="ioc-row"><span>URL</span><code>{doc.url}</code><CopyButton value={doc.url} onFail={(m) => toast(m, "error")} /></div>
              </div>
            )}
          </section>

          <section className="panel report-section">
            <h2>Podmioty i rejestr KNF</h2>
            <dl className="fact-list">
              <div><dt>Firma w reklamie</dt><dd>{firm?.name_in_ad || "—"}</dd></div>
              <div><dt>Oficjalna nazwa</dt><dd>{firm?.registry_match ? `${firm.registry_match.official_name} (ID KNF ${firm.registry_match.knf_id})` : "brak dopasowania w rejestrze KNF"}</dd></div>
              <div><dt>Autoryzacja</dt><dd>{yn(firm?.is_authorized)}</dd></div>
              <div><dt>Reklamujący</dt><dd>{adv?.name || "—"}</dd></div>
              <div><dt>Relacja</dt><dd>{RELATION[adv?.relation_to_firm] || "—"}</dd></div>
              <div><dt>Ujawnienie współpracy</dt><dd>{yn(adv?.disclosure_found)}</dd></div>
              <div><dt>Link afiliacyjny</dt><dd className="break-word">{adv?.affiliate_link ? String(adv.affiliate_link) : "—"}</dd></div>
            </dl>
          </section>

          <details className="panel raw-report">
            <summary>Reguły zgodne i nieocenione ({other.length})</summary>
            {GROUPS.map(([g, title]) => {
              const rs = other.filter((r) => groupOf(String(r.rule_id)) === g);
              return rs.length ? <Fragment key={g}><h3 className="section-note">{title}</h3><RulesTable rules={rs} /></Fragment> : null;
            })}
          </details>
        </div>

        <aside className="report-aside">
          {f.review && !editing
            ? <DecisionSummary f={f} labels={labels} onEdit={() => setEditing(true)} />
            : <ReviewPanel f={f} labels={labels} analyst={analyst} onReview={async (...a) => { await onReview(...a); setEditing(false); }} />}

          <section className="panel">
            <h2>Przypisanie i status</h2>
            <div className="assign-row">
              {f.assignee !== analyst && <button type="button" className="button secondary small" onClick={() => onAssign(f.id, analyst)}>{f.assignee ? "Przejmij" : "Zajmuję się"}</button>}
              {f.assignee === analyst && <button type="button" className="button ghost small" onClick={() => onAssign(f.id, null)}>Zwolnij</button>}
              <select aria-label="Przypisany analityk" value={f.assignee || ""} onChange={(e) => onAssign(f.id, e.target.value || null)}>
                <option value="">— nieprzypisane —</option>
                {[...new Set([...ANALYSTS, analyst, f.assignee].filter(Boolean))].map((a) => (
                  <option key={a} value={a}>{a}{a === f.ai_suggestion?.assignee ? " (sugestia AI)" : ""}</option>
                ))}
              </select>
              <select aria-label="Status" value={f.status} onChange={(e) => onStatus(f.id, e.target.value)}>
                {Object.entries(STATUS).filter(([k]) => !["confirmed", "dismissed"].includes(k) || k === f.status)
                  .map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <p className="section-note">„Potwierdzone” i „Odrzucone” ustawia wyłącznie ocena człowieka.</p>
          </section>

          <section className="panel">
            <h2>Źródło materiału</h2>
            <dl className="fact-list">
              <div><dt>Źródło</dt><dd>{sourceLabel(doc.source)}</dd></div>
              <div><dt>Publikujący</dt><dd>{publisherName(doc) || "—"}</dd></div>
              <div><dt>Język</dt><dd>{doc.lang || "—"}</dd></div>
              <div><dt>Wykryto</dt><dd>{fmtDate(f.created_at)}</dd></div>
            </dl>
            {doc.url && <code className="source-address">{doc.url}</code>}
            {url && <p className="source-note"><a className="text-link" href={url} target="_blank" rel="noreferrer noopener">Otwórz źródło ↗</a></p>}
          </section>

          <section className="panel">
            <h2>Historia zmian</h2>
            <div className="audit-event"><span /><div><strong>wykrycie przez system</strong><small>system · {fmtDate(f.created_at)}</small></div></div>
            {events.map((e, i) => (
              <div className="audit-event" key={i}><span /><div><strong>{describeEvent(e, labels)}</strong><small>{e.actor || "system"} · {fmtDate(e.at)}</small></div></div>
            ))}
            {ev.error && <p className="section-note">Historia niedostępna ({ev.error.message}).</p>}
          </section>

        </aside>
      </div>
    </>
  );
}
