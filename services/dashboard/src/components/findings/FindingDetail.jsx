import { RiskBadge } from "../common/Badge.jsx";
import StatusSelect from "./StatusSelect.jsx";
import { AssigneeSelect } from "./Assignee.jsx";
import Timeline from "./Timeline.jsx";
import ReviewActions, { AiSuggestion } from "./ReviewActions.jsx";
import { MODULE, fmtDate, publisherName, sourceLabel } from "../../lib/labels.js";

const VERDICT = { fail: "naruszenie", pass: "OK", not_applicable: "n/d", uncertain: "niepewne" };

export default function FindingDetail({ finding: f, labels, onUpdate, onReview, onAssign, currentUser }) {
  if (!f) return <div className="empty">Ładowanie…</div>;
  const firm = f.entities?.investment_firm;
  return (
    <div className="detail">
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
        <dt>Źródło</dt><dd>{sourceLabel(f.document?.source)} · <a href={f.document?.url} target="_blank" rel="noreferrer">{f.document?.url}</a></dd>
        <dt>Publikujący</dt><dd>{publisherName(f.document)}</dd>
        <dt>Wykryto</dt><dd>{fmtDate(f.created_at)}</dd>
        <dt>Moduły</dt><dd>{f.modules.map((m) => MODULE[m]).join(", ")}</dd>
        <dt>Routing</dt><dd>{f.routing?.rule} · {f.routing?.reason}</dd>
        <dt>Podmiot</dt>
        <dd>{firm?.name_in_ad} {firm?.registry_match ? `(KNF ${firm.registry_match.knf_id})` : <span className="tag warn">brak w rejestrze KNF</span>}</dd>
      </dl>
      <h4>Reguły ({f.rule_results.length})</h4>
      <table className="table compact">
        <thead><tr><th>Reguła</th><th>Silnik</th><th>Werdykt</th><th>Pewność</th><th>Dowód</th></tr></thead>
        <tbody>
          {f.rule_results.map((r) => (
            <tr key={r.rule_id} className={r.verdict === "fail" ? "row-fail" : ""}>
              <td>{r.rule_id}. {r.rule_name}</td>
              <td>{r.engine}</td>
              <td>{VERDICT[r.verdict] || r.verdict}</td>
              <td>{Math.round(r.confidence * 100)}%</td>
              <td>{r.evidence?.quote ? <q>{r.evidence.quote}</q> : r.evidence?.summary}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h4>Oś zdarzeń</h4>
      <Timeline finding={f} />
    </div>
  );
}
