import { RiskBadge } from "../common/Badge.jsx";
import StatusSelect from "./StatusSelect.jsx";
import { AssigneeSelect } from "./Assignee.jsx";
import Timeline from "./Timeline.jsx";
import ReviewActions, { AiSuggestion } from "./ReviewActions.jsx";
import { formatEvidence, safeHttpUrl } from "../../lib/evidence.js";
import { VERDICT, ENGINE, RELATION, GROUPS, groupOf } from "../../lib/detail.js";
import { MODULE, fmtDate, publisherName, sourceLabel } from "../../lib/labels.js";

const yn = (v) => (v == null ? "—" : v ? "tak" : "nie");

function summaryLabel(engine) {
  if (engine === "llm") return "AI · Bielik";
  if (engine === "template") return "szablon";
  return null;
}

function Evidence({ evidence }) {
  const e = formatEvidence(evidence);
  return (
    <div className="evidence">
      {e.quote && <q>{e.quote}</q>}
      {e.summary && <div>{e.summary}</div>}
      {e.measured.length > 0 && (
        <div className="muted">{e.measured.map((m) => `${m.key}: ${m.value}`).join(" · ")}</div>
      )}
      <div className="muted">
        {[e.viewport, e.timestamp && `czas ${e.timestamp}`].filter(Boolean).join(" · ")}
        {e.screenshot && <> <a href={e.screenshot} target="_blank" rel="noreferrer">zrzut</a></>}
      </div>
    </div>
  );
}

function RulesTable({ rules }) {
  return (
    <table className="table compact">
      <thead><tr><th>Reguła</th><th>Silnik</th><th>Podstawa prawna</th><th>Pewność</th><th>Waga</th><th>Dowód</th></tr></thead>
      <tbody>
        {rules.map((r) => (
          <tr key={r.rule_id} className={r.verdict === "fail" ? "row-fail" : ""}>
            <td>{r.rule_id}. {r.rule_name}{r.verdict !== "fail" && <div className="muted">{VERDICT[r.verdict] || r.verdict}</div>}</td>
            <td>{ENGINE[r.engine] || r.engine}</td>
            <td>{r.legal_basis || "—"}</td>
            <td>{Math.round((r.confidence ?? 0) * 100)}%</td>
            <td>{r.severity ?? "—"}</td>
            <td><Evidence evidence={r.evidence} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function FindingDetail({ finding: f, labels, onUpdate, onReview, onAssign, currentUser }) {
  if (!f) return <div className="empty">Ładowanie…</div>;
  const firm = f.entities?.investment_firm;
  const adv = f.entities?.advertiser;
  const rules = f.rule_results || [];
  const failed = rules.filter((r) => r.verdict === "fail");
  const label = summaryLabel(f.summary_engine);
  const affiliate = safeHttpUrl(adv?.affiliate_link);
  return (
    <div className="detail">
      <section className="summary">
        <h4>Podsumowanie {label && <span className="tag">{label}</span>}</h4>
        {f.summary ? <p>{f.summary}</p> : <p className="muted">Podsumowanie niedostępne</p>}
      </section>
      <div className="detail-row">
        <RiskBadge level={f.risk_level} score={f.risk_score} />
        <StatusSelect value={f.status} onChange={(s) => onUpdate(f.id, { status: s })} />
        <AssigneeSelect finding={f} currentUser={currentUser} onAssign={onAssign} />
      </div>
      <div className="decision">
        <h4>Decyzja człowieka <AiSuggestion suggestion={f.ai_suggestion} /></h4>
        <ReviewActions finding={f} labels={labels} currentUser={currentUser} onReview={onReview} />
      </div>
      <dl className="kv">
        <dt>Tytuł</dt><dd>{f.document?.title}</dd>
        <dt>Źródło</dt><dd>{sourceLabel(f.document?.source)} · {safeHttpUrl(f.document?.url) ? <a href={f.document.url} target="_blank" rel="noreferrer">{f.document.url}</a> : f.document?.url}</dd>
        <dt>Publikujący</dt><dd>{publisherName(f.document)}</dd>
        <dt>Wykryto</dt><dd>{fmtDate(f.created_at)}</dd>
        <dt>Moduły</dt><dd>{f.modules.map((m) => MODULE[m]).join(", ")}</dd>
        <dt>Routing</dt><dd>{f.routing?.rule} · {f.routing?.reason}</dd>
      </dl>
      <h4>Dlaczego ({failed.length})</h4>
      {failed.length ? <RulesTable rules={failed} /> : <div className="muted">Brak naruszonych reguł.</div>}
      <h4>Podmioty</h4>
      <dl className="kv">
        <dt>Firma w reklamie</dt><dd>{firm?.name_in_ad || "—"}</dd>
        <dt>Oficjalna nazwa</dt>
        <dd>{firm?.registry_match ? `${firm.registry_match.official_name} (ID KNF ${firm.registry_match.knf_id})` : <span className="tag warn">brak w rejestrze KNF</span>}</dd>
        <dt>Autoryzacja</dt><dd>{yn(firm?.is_authorized)}</dd>
        <dt>Reklamujący</dt><dd>{adv?.name || "—"}</dd>
        <dt>Relacja</dt><dd>{RELATION[adv?.relation_to_firm] || "—"}</dd>
        <dt>Ujawnienie współpracy</dt><dd>{yn(adv?.disclosure_found)}</dd>
        <dt>Link afiliacyjny</dt>
        <dd>{affiliate ? <a href={affiliate} target="_blank" rel="noreferrer">{affiliate}</a> : adv?.affiliate_link ? String(adv.affiliate_link) : "—"}</dd>
      </dl>
      <details className="all-rules">
        <summary>Wszystkie reguły ({rules.length})</summary>
        {GROUPS.map(([g, title]) => {
          const rs = rules.filter((r) => groupOf(String(r.rule_id)) === g);
          return rs.length ? <div key={g}><h5>{title}</h5><RulesTable rules={rs} /></div> : null;
        })}
      </details>
      <h4>Oś zdarzeń</h4>
      <Timeline finding={f} />
    </div>
  );
}
