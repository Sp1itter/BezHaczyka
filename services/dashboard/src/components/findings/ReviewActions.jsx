import { useState } from "react";
import { DECISION, fmtDate } from "../../lib/labels.js";

// Sugestia modelu (jesli jest). Decyzja zawsze nalezy do czlowieka.
export function AiSuggestion({ suggestion: s }) {
  if (!s) return null;
  return (
    <span className="ai-suggestion" title="Sugestia modelu, wymaga decyzji człowieka">
      AI: {DECISION[s.status]} · {Math.round(s.confidence * 100)}%
    </span>
  );
}

const GROUPS = { tp: "Naruszenie", fn: "Naruszenie", fp: "Brak naruszenia", other: "Inne" };

// Ocena czlowieka: rozwijana lista etykiet feedbacku (TP, FP, bledny podmiot, ...) + notatka.
// labels: [{ value, label, verdict, group }] z GET /review-labels.
export default function ReviewActions({ finding: f, labels = [], currentUser, onReview, compact }) {
  const [label, setLabel] = useState("");
  const [note, setNote] = useState("");
  const [editing, setEditing] = useState(false);
  const byValue = Object.fromEntries(labels.map((l) => [l.value, l]));

  if (f.review && !editing)
    return (
      <span className="review-done" onClick={(e) => e.stopPropagation()}>
        <span className={`badge verdict-${f.review.decision}`}>{DECISION[f.review.decision]}</span>{" "}
        {byValue[f.review.label]?.label || f.review.label}
        <span className="muted"> · {f.review.by} · {fmtDate(f.review.at)}{f.review.note ? ` · „${f.review.note}”` : ""}</span>
        {!compact && <button className="btn link" onClick={() => setEditing(true)}>Zmień ocenę</button>}
      </span>
    );

  const groups = labels.reduce((acc, l) => ((acc[GROUPS[l.group] || "Inne"] ||= []).push(l), acc), {});
  const save = () => { if (label) { onReview(f.id, label, note); setEditing(false); setLabel(""); setNote(""); } };
  return (
    <span className="review-actions" onClick={(e) => e.stopPropagation()}>
      <select value={label} onChange={(e) => setLabel(e.target.value)} className="review-select">
        <option value="">— ocena człowieka —</option>
        {Object.entries(groups).map(([g, items]) => (
          <optgroup key={g} label={g}>
            {items.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
          </optgroup>
        ))}
      </select>
      {(!compact || label) && (
        <input placeholder={label === "other" ? "Opisz błąd (wymagane)" : "Notatka (opcjonalnie)"} value={note} onChange={(e) => setNote(e.target.value)} />
      )}
      <button className={`btn ${byValue[label]?.verdict === "dismissed" ? "dismiss" : "confirm"}`}
        disabled={!label || (label === "other" && !note.trim())} onClick={save} title={`Zapisze jako ${currentUser}`}>
        Zapisz ocenę
      </button>
    </span>
  );
}
