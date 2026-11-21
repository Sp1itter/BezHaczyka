import Panel from "../components/common/Panel.jsx";
import StatTile from "../components/common/StatTile.jsx";
import { RiskBadge } from "../components/common/Badge.jsx";
import ReviewActions, { AiSuggestion } from "../components/findings/ReviewActions.jsx";
import { AssigneeSelect } from "../components/findings/Assignee.jsx";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { SOURCE, fmtDate } from "../lib/labels.js";

// Kolejka weryfikacji: wszystko z wynikiem >= progu z Kalibracji, bez decyzji czlowieka.
// Model zaweza prace (score, sugestia), ale potwierdzenie i przypisanie zatwierdza czlowiek.
export default function Review({ query, reloadKey, threshold, currentUser, onOpen, onReview, onAssign, onGoCalibration }) {
  const pendingQ = { ...query, min_score: threshold, reviewed: "false" };
  const doneQ = { ...query, min_score: threshold, reviewed: "true" };
  const pending = useApi(() => api.findings(pendingQ), [JSON.stringify(pendingQ) + reloadKey]);
  const done = useApi(() => api.findings(doneQ), [JSON.stringify(doneQ) + reloadKey]);
  const items = pending.data?.items || [];
  const reviewed = done.data?.items || [];
  const agree = reviewed.filter((f) => f.ai_suggestion?.status === f.review?.decision).length;
  return (
    <div className="grid">
      <div className="tiles span-12">
        <StatTile label="Czeka na decyzję człowieka" value={pending.data?.total ?? "…"} color="#d6bf57" />
        <StatTile label="Potwierdzone przez człowieka" value={reviewed.filter((f) => f.review.decision === "confirmed").length} color="#e7664c" />
        <StatTile label="Odrzucone jako fałszywy alarm" value={reviewed.filter((f) => f.review.decision === "dismissed").length} />
        <StatTile label="Zgodność AI z człowiekiem" value={reviewed.length ? `${Math.round((agree / reviewed.length) * 100)}%` : "—"} />
      </div>
      <Panel
        className="span-12"
        title={`Do weryfikacji: wynik ≥ ${threshold}`}
        actions={<button className="btn link" onClick={onGoCalibration}>Zmień próg w Kalibracji</button>}
      >
        {!items.length ? <div className="empty">Brak rekordów powyżej progu bez decyzji.</div> : (
          <table className="table">
            <thead>
              <tr><th>Wykryto</th><th>Ryzyko</th><th>Materiał</th><th>Sugestia AI</th><th>Przypisanie</th><th>Decyzja ({currentUser})</th></tr>
            </thead>
            <tbody>
              {items.map((f) => (
                <tr key={f.id} onClick={() => onOpen(f.id)}>
                  <td className="nowrap">{fmtDate(f.created_at)}</td>
                  <td><RiskBadge level={f.risk_level} score={f.risk_score} /></td>
                  <td>
                    <div className="cell-title">{f.document?.title}</div>
                    <div className="muted">{SOURCE[f.document?.source]} · {f.document?.publisher}</div>
                  </td>
                  <td><AiSuggestion suggestion={f.ai_suggestion} /></td>
                  <td><AssigneeSelect finding={f} onAssign={onAssign} /></td>
                  <td><ReviewActions finding={f} currentUser={currentUser} onReview={onReview} compact /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </div>
  );
}
