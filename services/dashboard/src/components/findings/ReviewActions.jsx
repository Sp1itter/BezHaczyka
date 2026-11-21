import { useState } from "react";
import { DECISION, fmtDate } from "../../lib/labels.js";

// Decyzja czlowieka. Model tylko podpowiada (ai_suggestion), zapis wymaga klikniecia analityka.
export function AiSuggestion({ suggestion: s }) {
  if (!s) return null;
  return (
    <span className="ai-suggestion" title="Sugestia modelu, wymaga decyzji człowieka">
      AI: {DECISION[s.status]} · {Math.round(s.confidence * 100)}%
    </span>
  );
}

export default function ReviewActions({ finding: f, currentUser, onReview, compact }) {
  const [note, setNote] = useState("");
  if (f.review)
    return (
      <span className="muted">
        {DECISION[f.review.decision]} przez <strong>{f.review.by}</strong> · {fmtDate(f.review.at)}
        {f.review.note ? ` · „${f.review.note}”` : ""}
      </span>
    );
  return (
    <span className="review-actions" onClick={(e) => e.stopPropagation()}>
      {!compact && (
        <input placeholder="Notatka (opcjonalnie)" value={note} onChange={(e) => setNote(e.target.value)} />
      )}
      <button className="btn confirm" onClick={() => onReview(f.id, "confirmed", note)} title={`Zapisze jako ${currentUser}`}>
        Potwierdź alert
      </button>
      <button className="btn dismiss" onClick={() => onReview(f.id, "dismissed", note)} title={`Zapisze jako ${currentUser}`}>
        Fałszywy alarm
      </button>
    </span>
  );
}
