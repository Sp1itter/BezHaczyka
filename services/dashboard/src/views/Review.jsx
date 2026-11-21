import Panel from "../components/common/Panel.jsx";
import StatTile from "../components/common/StatTile.jsx";
import { RiskBadge } from "../components/common/Badge.jsx";
import ReviewActions, { AiSuggestion } from "../components/findings/ReviewActions.jsx";
import { AssigneeSelect } from "../components/findings/Assignee.jsx";
import Breakdown from "../components/charts/Breakdown.jsx";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { fmtDate, publisherName, sourceLabel } from "../lib/labels.js";

// Kolejka weryfikacji: wszystko z wynikiem >= progu z Kalibracji, bez decyzji czlowieka.
// Model zaweza prace (score, sugestia), ale potwierdzenie i przypisanie zatwierdza czlowiek.
export default function Review({ query, reloadKey, threshold, labels, currentUser, onOpen, onReview, onAssign, onGoCalibration }) {
  const pendingQ = { ...query, min_score: threshold, reviewed: "false" };
  const doneQ = { ...query, min_score: threshold, reviewed: "true" };
  const pending = useApi(() => api.findings(pendingQ), [JSON.stringify(pendingQ) + reloadKey]);
  const done = useApi(() => api.findings(doneQ), [JSON.stringify(doneQ) + reloadKey]);
  const items = pending.data?.items || [];
  const reviewed = done.data?.items || [];
  const allReviewedQ = { ...query, reviewed: "true" };
  const allReviewed = useApi(() => api.findings(allReviewedQ), [JSON.stringify(allReviewedQ) + reloadKey]);
  const labelText = Object.fromEntries((labels || []).map((l) => [l.value, l.label]));
  const feedback = (allReviewed.data?.items || []).reduce((acc, f) => {
    const k = f.review?.label || f.status;
    acc[k] = (acc[k] || 0) + 1;
    return acc;
  }, {});
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
              <tr><th>Wykryto</th><th>Ryzyko</th><th>Materiał</th><th>Sugestia AI</th><th>Kto się zajmuje</th><th>Ocena ({currentUser})</th></tr>
            </thead>
            <tbody>
              {items.map((f) => (
                <tr key={f.id} onClick={() => onOpen(f.id)}>
                  <td className="nowrap">{fmtDate(f.created_at)}</td>
                  <td><RiskBadge level={f.risk_level} score={f.risk_score} /></td>
                  <td>
                    <div className="cell-title">{f.document?.title}</div>
                    <div className="muted">{sourceLabel(f.document?.source)} · {publisherName(f.document)}</div>
                  </td>
                  <td><AiSuggestion suggestion={f.ai_suggestion} /></td>
                  <td><AssigneeSelect finding={f} currentUser={currentUser} onAssign={onAssign} /></td>
                  <td><ReviewActions finding={f} labels={labels} currentUser={currentUser} onReview={onReview} compact /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
      <Panel title="Feedback analityków (etykiety ocen)" className="span-12">
        {Object.keys(feedback).length ? <Breakdown data={feedback} labels={labelText} height={40 + 28 * Object.keys(feedback).length} />
          : <div className="empty">Brak ocen w wybranym zakresie.</div>}
      </Panel>
    </div>
  );
}
